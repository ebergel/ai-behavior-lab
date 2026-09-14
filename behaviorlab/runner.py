"""Synthetic campaign execution and recovery. No network or live inference."""

from pathlib import Path

from . import __version__
from .common import canonical, fingerprint, read_json, require
from .history import Turn, request
from .journal import Journal, read_events, rebuild_index
from .protocol import Protocol, Registry

PARSER_VERSION = "ollama-shaped-fixture/1"


class NeedsAttention(RuntimeError):
    pass


class FakeBackend:
    identity = "deterministic-fake/1"

    def __init__(self):
        self.calls = 0

    def generate(self, payload):
        self.calls += 1
        return canonical({"model": payload["model"], "fixture": True, "done": True,
                          "done_reason": "stop", "message": {"role": "assistant",
                          "content": "[SYNTHETIC FIXTURE] request " + fingerprint(payload)[:20]}})


def parse_response(raw, payload):
    data = read_json(raw)
    require(isinstance(data, dict) and data.get("done") is True, "Incomplete response")
    require(data.get("model") == payload["model"], "Response model mismatch")
    message = data.get("message")
    require(isinstance(message, dict) and message.get("role") == "assistant", "Missing assistant response")
    require(isinstance(message.get("content"), str), "Missing or non-text content")
    thinking = message.get("thinking")
    require(thinking is None or isinstance(thinking, str), "Invalid thinking field")
    require(data.get("done_reason") in ("stop", "length"), "Unknown finish reason")
    reason = None
    if data["done_reason"] == "length":
        reason = "output_cap"
    elif data.get("context_truncated") is True:
        reason = "context_truncated"
    elif not payload["think"] and thinking:
        reason = "unexpected_thinking_output"
    return {"content": message["content"], "thinking": thinking, "invalid_reason": reason}


class State:
    def __init__(self, events):
        self.meta = None
        self.requests = {}
        self.attempts = {}
        self.responses = {}
        self.errors = {}
        self.retried = set()
        self.outcomes = {}
        self.complete = False
        for e in events:
            kind, p = e["kind"], e["payload"]
            if kind == "campaign_created":
                require(self.meta is None and e["seq"] == 1, "Invalid campaign header")
                self.meta = p
                continue
            require(self.meta is not None, "Event without campaign header")
            if kind == "request_saved":
                node, attempt = p["node_id"], p["attempt_id"]
                require(attempt not in self.requests and node not in self.outcomes, "Duplicate request or completed node")
                prior = self.attempts.get(node)
                require(prior is None or prior in self.retried, "Retry without explicit resolution event")
                require(p["request_sha256"] == fingerprint(p["request"]), "Request checksum mismatch")
                self.requests[attempt] = p
                self.attempts[node] = attempt
            elif kind in ("response_saved", "request_error"):
                attempt = p["attempt_id"]
                require(attempt in self.requests and attempt not in self.responses and attempt not in self.errors,
                        "Duplicate or unrequested response")
                require(attempt not in self.retried, "Response for an abandoned attempt")
                require(p["node_id"] == self.requests[attempt]["node_id"], "Response attached to wrong node")
                (self.responses if kind == "response_saved" else self.errors)[attempt] = p
            elif kind == "attempt_retry_authorized":
                attempt = p["attempt_id"]
                require(attempt in self.requests and attempt not in self.responses and attempt not in self.retried,
                        "Cannot retry an answered or resolved attempt")
                require(self.attempts[p["node_id"]] == attempt, "Retry references wrong attempt")
                self.retried.add(attempt)
            elif kind in ("turn_committed", "turn_invalid", "node_blocked"):
                node = p["node_id"]
                require(node not in self.outcomes, "Duplicate node outcome")
                if kind != "node_blocked":
                    require(p["attempt_id"] in self.responses, "Outcome without saved raw response")
                    require(self.attempts[node] == p["attempt_id"], "Outcome references wrong attempt")
                self.outcomes[node] = (kind, p)
            elif kind == "campaign_complete":
                require(not self.complete, "Duplicate completion")
                self.complete = True
            elif kind != "campaign_paused":
                raise ValueError("Unknown journal event: " + kind)
        require(self.meta is not None, "Empty campaign")


def create_campaign(directory, protocol, registry):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    with Journal(directory, create=True) as journal:
        journal.append("campaign_created", {
            "software_version": __version__, "backend": FakeBackend.identity,
            "data_class": "synthetic_engineering_fixture_not_behavioral_evidence",
            "protocol": read_json(protocol.document_json), "protocol_sha256": protocol.digest,
            "registry": read_json(registry.document_json), "registry_sha256": registry.digest,
            "parser_version": PARSER_VERSION, "planned_nodes": len(protocol.nodes())})
        rebuild_index(directory, journal.events)


def campaign_documents(events):
    state = State(events)
    registry = Registry.from_dict(state.meta["registry"])
    protocol = Protocol.from_dict(state.meta["protocol"], registry)
    require(registry.digest == state.meta["registry_sha256"] and protocol.digest == state.meta["protocol_sha256"],
            "Campaign identity mismatch")
    require(state.meta["parser_version"] == PARSER_VERSION, "Parser version changed; explicit migration required")
    require(state.meta["backend"] == FakeBackend.identity and
            state.meta["data_class"] == "synthetic_engineering_fixture_not_behavioral_evidence",
            "Unsupported campaign backend or data class")
    nodes = {n.id: n for n in protocol.nodes()}
    require(state.meta["planned_nodes"] == len(nodes), "Campaign budget differs from its graph")
    require(set(state.outcomes).issubset(nodes), "Outcome for a node outside the protocol")
    require(all(p["node_id"] in nodes for p in state.requests.values()), "Request outside protocol")
    if state.complete:
        require(set(state.outcomes) == set(nodes), "Completion recorded before all nodes are accounted for")
    return protocol, registry, state


def execute(directory, backend=None, max_calls=None, retry_unresolved=False, hook=None):
    """A hook is solely for injected crash tests at durability boundaries."""
    backend = backend or FakeBackend()
    require(backend.identity == FakeBackend.identity, "Milestone 1 only supports the fake backend")
    require(max_calls is None or type(max_calls) is int and max_calls >= 0, "Invalid call limit")
    calls = 0
    with Journal(directory) as journal:
        protocol, registry, state = campaign_documents(journal.events)
        turns = {}
        outcomes = dict(state.outcomes)
        for node in protocol.nodes():
            previous = outcomes.get(node.id)
            if node.parent and node.parent in outcomes and outcomes[node.parent][0] != "turn_committed":
                if previous:
                    require(previous[0] == "node_blocked" and previous[1]["parent_id"] == node.parent,
                            "Invalid descendant of a failed node")
                else:
                    p = {"node_id": node.id, "parent_id": node.parent, "reason": "parent_unavailable"}
                    journal.append("node_blocked", p)
                    outcomes[node.id] = ("node_blocked", p)
                continue
            payload = request(protocol, registry, node, turns)
            attempt = state.attempts.get(node.id)
            if attempt is not None:
                saved = state.requests[attempt]
                require(saved["request"] == payload and saved["model_digest"] == registry.model(node.model).digest,
                        "Saved request does not match reconstructed protocol/history")
            if previous:
                require(previous[0] != "node_blocked", "Unexpected blocked node")
                raw = state.responses[attempt]["raw_response"]
                expected_kind, expected = outcome(node, attempt, raw, payload)
                require(previous == (expected_kind, expected), "Stored outcome differs from raw response")
                if expected_kind == "turn_committed":
                    turns[node.id] = turn_from(node, expected)
                continue
            if attempt is not None and attempt not in state.responses:
                if attempt not in state.retried:
                    if not retry_unresolved:
                        raise NeedsAttention("Unresolved attempt " + attempt + "; inspect its journal before explicitly retrying")
                    journal.append("attempt_retry_authorized", {"node_id": node.id, "attempt_id": attempt,
                                   "reason": "explicit_retry_unresolved_flag", "original_outcome": "unknown_or_error"})
            if attempt is None or attempt not in state.responses:
                if max_calls is not None and calls >= max_calls:
                    journal.append("campaign_paused", {"reason": "call_budget", "new_calls": calls})
                    rebuild_index(directory, journal.events)
                    return summarize_events(journal.events)
                number = 1 + sum(p["node_id"] == node.id for p in state.requests.values())
                attempt = node.id + "/attempt-" + str(number)
                p = {"node_id": node.id, "attempt_id": attempt, "request": payload,
                     "request_sha256": fingerprint(payload), "model_label": node.model,
                     "model_digest": registry.model(node.model).digest, "parent_id": node.parent,
                     "root_id": node.root, "segment": node.segment, "global_turn": node.turn,
                     "speaker": node.speaker, "history_policy": node.history}
                journal.append("request_saved", p)
                if hook:
                    hook("after_request", node)
                try:
                    raw = backend.generate(payload)
                    require(isinstance(raw, str), "Backend must return raw response text")
                except Exception as exc:
                    journal.append("request_error", {"node_id": node.id, "attempt_id": attempt,
                                   "error_type": type(exc).__name__, "error": str(exc)})
                    rebuild_index(directory, journal.events)
                    raise NeedsAttention("Backend failure saved for " + attempt) from exc
                calls += 1
                journal.append("response_saved", {"node_id": node.id, "attempt_id": attempt, "raw_response": raw})
                if hook:
                    hook("after_response", node)
            else:
                raw = state.responses[attempt]["raw_response"]
            kind, result = outcome(node, attempt, raw, payload)
            journal.append(kind, result)
            outcomes[node.id] = (kind, result)
            if kind == "turn_committed":
                turns[node.id] = turn_from(node, result)
            if hook:
                hook("after_commit", node)
        if not state.complete:
            journal.append("campaign_complete", {"planned_nodes": len(protocol.nodes()), "accounted_nodes": len(outcomes)})
        rebuild_index(directory, journal.events)
        return summarize_events(journal.events)


def outcome(node, attempt, raw, payload):
    p = {"node_id": node.id, "attempt_id": attempt, "parent_id": node.parent,
         "root_id": node.root, "segment": node.segment, "global_turn": node.turn,
         "speaker": node.speaker, "parser_version": PARSER_VERSION}
    try:
        parsed = parse_response(raw, payload)
    except (ValueError, TypeError, KeyError) as exc:
        p["reason"] = "malformed_response"
        p["detail"] = str(exc)
        return "turn_invalid", p
    if parsed["invalid_reason"]:
        p["reason"] = parsed["invalid_reason"]
        return "turn_invalid", p
    p.update(content=parsed["content"], thinking=parsed["thinking"])
    return "turn_committed", p


def turn_from(node, p):
    return Turn(node.id, node.parent, node.root, node.turn, node.speaker, p["content"], p["thinking"])


def summarize_events(events):
    protocol, registry, state = campaign_documents(events)
    kinds = [kind for kind, p in state.outcomes.values()]
    unresolved = [a for a in state.attempts.values() if a not in state.responses and a not in state.retried]
    return {"data_class": state.meta["data_class"], "backend": state.meta["backend"],
            "protocol_sha256": protocol.digest, "registry_sha256": registry.digest,
            "planned_nodes": len(protocol.nodes()), "committed_turns": kinds.count("turn_committed"),
            "invalid_turns": kinds.count("turn_invalid"), "blocked_nodes": kinds.count("node_blocked"),
            "unresolved_attempts": unresolved, "requests": len(state.requests), "responses": len(state.responses),
            "complete": state.complete, "journal_events": len(events), "journal_head": events[-1]["hash"]}


def summarize(directory):
    return summarize_events(read_events(Path(directory) / "events.jsonl"))
