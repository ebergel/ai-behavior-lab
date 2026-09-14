"""Participant-specific API histories derived from immutable actual ancestry."""

from dataclasses import dataclass
from typing import Optional

from .common import read_json, require


@dataclass(frozen=True)
class Turn:
    node_id: str
    parent_id: Optional[str]
    root: str
    number: int
    speaker: str
    content: str
    thinking: Optional[str]


def ancestry(parent_id, turns):
    reverse = []
    seen = set()
    while parent_id is not None:
        require(parent_id not in seen, "Cycle in conversation ancestry")
        seen.add(parent_id)
        turn = turns[parent_id]
        reverse.append(turn)
        parent_id = turn.parent_id
    return tuple(reversed(reverse))


def messages(protocol, history, speaker, policy):
    require(speaker in ("X", "Y") and policy in ("F", "R"), "Invalid history projection")
    for i, turn in enumerate(history, 1):
        require(turn.number == i and turn.speaker == ("X" if i % 2 else "Y"), "Invalid conversation sequence")
        require(turn.root == history[0].root, "History crosses independent roots")
        require(turn.parent_id == (history[i-2].node_id if i > 1 else None), "Broken actual-history chain")
    selected = history if policy == "F" else history[-protocol.recent_messages:]
    result = [{"role": "system", "content": protocol.system}]
    if speaker == "X" and policy == "F":
        result.append({"role": "user", "content": protocol.opening})
    for turn in selected:
        result.append({"role": "assistant" if turn.speaker == speaker else "user", "content": turn.content})
    return result


def request(protocol, registry, node, turns):
    history = ancestry(node.parent, turns)
    require(len(history) == node.turn - 1, "Incomplete ancestry for request")
    if history:
        require(history[0].root == node.root, "Cross-root parent")
    payload = read_json(protocol.settings_json)
    payload["model"] = registry.model(node.model).tag
    payload["messages"] = messages(protocol, history, node.speaker, node.history)
    payload["options"]["seed"] = node.seed
    return payload
