"""Supported WebUI login, discovery, and a display-only transcript mirror."""

import os
from pathlib import Path
import time
import uuid

from .backends import json_request, validate_endpoint, LOOPBACK
from .common import canonical, fingerprint, read_json, require
from .journal import read_events
from .runner import campaign_documents


def login_local(endpoint, token_file):
    require(validate_endpoint(endpoint).hostname in LOOPBACK, "Automatic single-user sign-in is local only")
    config = json_request(endpoint, "/api/config")
    require(config.get("features", {}).get("auth") is False,
            "This server requires normal sign-in; provide a session token or API key via an environment variable")
    session = json_request(endpoint, "/api/v1/auths/signin", {"email": "", "password": ""})
    require(isinstance(session.get("token"), str) and session["token"], "Sign-in did not return a session")
    path = Path(token_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(session["token"])
    return {"authenticated": True, "role": session.get("role"), "token_file": str(path.resolve()),
            "api_key_setting_changed": False}


def catalog(endpoint, token):
    data = json_request(endpoint, "/api/models", token=token)
    return [{k: r.get(k) for k in ("id", "name", "owned_by", "urlIdx", "connection_type", "pipe")}
            for r in data["data"]]


def export_transcript(directory, leaf):
    events = read_events(Path(directory) / "events.jsonl")
    protocol, registry, state = campaign_documents(events)
    nodes = {n.id: n for n in protocol.nodes()}
    require(leaf in nodes, "Unknown leaf node")
    # Replay validates every saved outcome against raw evidence without needing credentials/network.
    # Do not mutate the journal during export.
    from .history import request, Turn
    from .runner import outcome
    turns = {}
    chain = []
    current = leaf
    while current is not None:
        require(current in state.outcomes and state.outcomes[current][0] == "turn_committed", "Leaf ancestry is incomplete or invalid")
        chain.append(nodes[current])
        current = nodes[current].parent
    chain.reverse()
    live = state.meta["backend"] != "deterministic-fake/1"
    for node in chain:
        p = state.outcomes[node.id][1]
        saved = state.requests[p["attempt_id"]]
        payload = request(protocol, registry, node, turns)
        require(saved["request"] == payload, "Saved history differs from reconstructed ancestry")
        response = state.responses[p["attempt_id"]]
        expected = outcome(node, p["attempt_id"], response["raw_response"], payload,
                           registry.model(node.model) if live else None, response.get("transport"), state.meta["parser_version"])
        require(expected == state.outcomes[node.id], "Saved outcome differs from raw evidence")
        turns[node.id] = Turn(node.id, node.parent, node.root, node.turn, node.speaker, p["content"], p["thinking"])
    head = events[-1]["hash"]
    identity = {"journal_head": head, "leaf": leaf, "protocol_sha256": protocol.digest,
                "data_class": state.meta["data_class"], "display_only": True}
    stamp = int(time.time())
    export_id = fingerprint(identity)
    def mid(value):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, export_id + ":" + value))
    intro = ("Laboratory transcript — " + state.meta["data_class"] + "\n\n"
             "Both X and Y are AI participants. User/assistant display roles are layout only. "
             "This is a view of one actual branch. Edits and continuations in WebUI are exploratory; "
             "the laboratory journal remains authoritative.\n\nProtocol: " + protocol.digest + "\nBranch: " + leaf)
    display = [{"id": mid("intro"), "role": "user", "content": intro, "parentId": None,
                "childrenIds": [], "timestamp": stamp}]
    for node in chain:
        model = registry.model(node.model)
        text = "**" + node.speaker + " · " + model.tag + " · turn " + str(node.turn) + "**\n\n" + turns[node.id].content
        display.append({"id": mid(node.id), "role": "assistant" if node.speaker == "X" else "user",
                        "content": text, "parentId": display[-1]["id"], "childrenIds": [], "timestamp": stamp,
                        "model": model.tag, "modelName": node.speaker + " · " + model.tag,
                        "done": True, "lab_node_id": node.id})
        display[-2]["childrenIds"] = [display[-1]["id"]]
    label = 'qualification' if read_json(protocol.document_json)['schema'] == 'behaviorlab.protocol/3' else 'local engineering' if live else 'synthetic'
    chat = {"title": "Behavior Lab · " + label + " · " + leaf,
            "models": list(dict.fromkeys(registry.model(n.model).tag for n in chain)),
            "messages": display, "history": {"messages": {m["id"]: m for m in display}, "currentId": display[-1]["id"]},
            "params": {}, "timestamp": stamp * 1000, "lab_evidence": identity}
    return {"chats": [{"chat": chat, "meta": {"behaviorlab_export_id": export_id},
                       "current_message_id": display[-1]["id"], "created_at": stamp, "updated_at": stamp}]}


def import_transcript(endpoint, token, document, receipt_file):
    """A pending receipt prevents an uncertain import from silently duplicating a chat."""
    path = Path(receipt_file)
    digest = fingerprint(document)
    if path.exists():
        receipt = read_json(path.read_text())
        require(receipt["document_sha256"] == digest and receipt["endpoint"] == endpoint, "Import receipt identity mismatch")
        require(receipt.get("chat_id"), "An earlier import has an unknown outcome; inspect WebUI before resolving its receipt")
        if receipt.get("round_trip_verified"):
            return receipt
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {"document_sha256": digest, "endpoint": endpoint, "status": "pending"}
        with path.open("x") as f:
            f.write(canonical(receipt) + "\n")
            f.flush()
            os.fsync(f.fileno())
        result = json_request(endpoint, "/api/v1/chats/import", document, token)
        require(isinstance(result, list) and len(result) == 1 and result[0].get("id"), "Unexpected import result")
        receipt.update(chat_id=result[0]["id"], status="imported", url=endpoint.rstrip("/") + "/c/" + result[0]["id"])
        save_receipt(path, receipt)
    saved = json_request(endpoint, "/api/v1/chats/" + receipt["chat_id"], token=token)
    original = document["chats"][0]["chat"]
    require(saved["chat"]["history"] == original["history"], "Imported transcript differs from exported history")
    receipt["round_trip_verified"] = True
    save_receipt(path, receipt)
    return receipt


def save_receipt(path, receipt):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x") as f:
        f.write(canonical(receipt) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)
