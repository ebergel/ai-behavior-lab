"""Validated, immutable protocols and pinned model configurations.

Versions 1/2 execute synthetic/local engineering; version 3 explicitly admits
bounded qualification screens. The factorial research proposal remains separate.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Tuple

from .common import canonical, fingerprint, read_json, require, sha256

IDENTIFIER = re.compile(r"[A-Za-z0-9_-]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def identifier(value):
    require(isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)),
            "Invalid identifier: " + repr(value))
    return value


def integer(value, low, high, name):
    require(type(value) is int and low <= value <= high, "Invalid " + name)
    return value


@dataclass(frozen=True)
class Model:
    label: str
    tag: str
    digest: Optional[str]
    metadata_json: str


@dataclass(frozen=True)
class Registry:
    document_json: str
    models: Tuple[Model, ...]

    @classmethod
    def from_dict(cls, document):
        require(document.get("schema") in ("behaviorlab.models/1", "behaviorlab.models/2"), "Unsupported model registry")
        live = document["schema"] == "behaviorlab.models/2"
        models = []
        for row in document["models"]:
            label = identifier(row["label"])
            require(isinstance(row["tag"], str) and row["tag"], "Missing model tag")
            if live:
                from .backends import validate_model
                validate_model(row)
            else:
                require(bool(HEX.fullmatch(row["digest"])), "A full model digest is required")
                require(bool(HEX.fullmatch(row["template_sha256"])), "Missing template fingerprint")
                require(isinstance(row.get("template"), str) and
                        sha256(row["template"].encode("utf-8")) == row["template_sha256"],
                        "Archived template does not match its fingerprint")
            models.append(Model(label, row["tag"], row["digest"], canonical(row)))
        require(models and len({m.label for m in models}) == len(models), "Duplicate/empty model labels")
        return cls(canonical(document), tuple(models))

    @classmethod
    def load(cls, path):
        return cls.from_dict(read_json(Path(path).read_text()))

    @property
    def digest(self):
        return fingerprint(read_json(self.document_json))

    def model(self, label):
        return next(m for m in self.models if m.label == label)

    def verify_observation(self, label, tag, digest):
        model = self.model(label)
        require((model.tag, model.digest) == (tag, digest), "Model artifact drift for " + label)


@dataclass(frozen=True)
class Segment:
    name: str
    parent: Optional[str]
    start: int
    stop: int
    history: str


@dataclass(frozen=True)
class Root:
    name: str
    pairing_index: int
    root_index: int
    x_model: str
    y_model: str
    order: Tuple[str, ...]


@dataclass(frozen=True)
class Node:
    id: str
    root: str
    segment: str
    turn: int
    speaker: str
    model: str
    parent: Optional[str]
    history: str
    seed: int


@dataclass(frozen=True)
class Protocol:
    document_json: str
    registry_digest: str
    system: str
    opening: str
    settings_json: str
    recent_messages: int
    seed_base: int
    roots: Tuple[Root, ...]
    segments: Tuple[Segment, ...]

    @classmethod
    def from_dict(cls, d, registry):
        fields = {"schema", "id", "execution_class", "registry_sha256", "system_prompt",
                  "opening_X", "settings", "recent_messages", "seed_base", "roots", "segments"}
        qualification = d.get('schema') == 'behaviorlab.protocol/3'
        if qualification:
            fields.add('qualification')
        require(set(d) == fields, "Unexpected or missing protocol fields")
        require(d["schema"] in ("behaviorlab.protocol/1", "behaviorlab.protocol/2", "behaviorlab.protocol/3"), "Unsupported protocol schema")
        live = d["schema"] != "behaviorlab.protocol/1"
        require(d["execution_class"] == ('qualification_local' if qualification else "engineering_local" if live else "engineering_fake_only"),
                "Execution class differs from protocol schema")
        if qualification:
            q = d['qualification']
            require(isinstance(q, dict) and set(q) == {'stage', 'decisions'}
                    and q['stage'] in ('historical_reference', 'common_protocol'),
                    'Declare qualification stage')
            policy = q['decisions']
            require(isinstance(policy, dict) and policy.get('schema') == 'behaviorlab.qualification-decisions/1'
                    and policy.get('main_pilot_enabled') is False
                    and policy.get('no_adaptive_replacements') is True
                    and policy.get('word_policy') == 'flag_preserve_continue'
                    and policy.get('semantic_window') == [25, 30]
                    and policy.get('semantic_rule') == 'one_explicit_self_endorsement_each_speaker_same_window',
                    'Qualification requires explicit frozen decisions; no pilot execution')
            require(len(d['segments']) == 1 and d['segments'][0] ==
                    {'id': 'prefix', 'parent': None, 'start': 1, 'stop': 30, 'history': 'F'}
                    and 1 <= len(d['roots']) <= 4 and all(r['X'] == r['Y'] for r in d['roots']),
                    'Qualification is bounded to at most four homogeneous 30-message roots')
        require(read_json(registry.document_json)["schema"] == ("behaviorlab.models/2" if live else "behaviorlab.models/1"),
                "Protocol and registry schema versions differ")
        identifier(d["id"])
        require(d["registry_sha256"] == registry.digest, "Protocol/model registry fingerprint mismatch")
        for field in ["system_prompt", "opening_X"]:
            require(isinstance(d[field], str) and d[field], "Missing " + field)
        integer(d["recent_messages"], 1, 99, "recent history length")
        require(d["recent_messages"] % 2 == 1, "Recent history must preserve alternating roles and end in user")
        integer(d["seed_base"], 0, 2**30, "seed base")
        settings = d["settings"]
        if live:
            from .backends import validate_settings
            validate_settings(settings, registry)
        else:
            cls.validate_ollama_settings(settings)
        return cls.compile_graph(d, registry, settings)

    @staticmethod
    def validate_ollama_settings(settings):
        require(set(settings) == {"think", "stream", "keep_alive", "options"}, "Unsupported request settings")
        require(type(settings["think"]) is bool and settings["stream"] is False, "Invalid thinking/stream mode")
        require(isinstance(settings["keep_alive"], str) and settings["keep_alive"], "Invalid keep_alive")
        options = settings["options"]
        require(set(options) == {"num_ctx", "num_predict", "temperature", "top_p", "top_k", "min_p",
                                 "repeat_penalty", "repeat_last_n", "presence_penalty", "frequency_penalty"},
                "Explicit sampling options required; unrecognized options are not silently ignored")
        integer(options["num_ctx"], 1, 10**7, "context size")
        integer(options["num_predict"], 1, options["num_ctx"], "output budget")
        integer(options["top_k"], 0, 10**7, "top_k")
        integer(options["repeat_last_n"], 0, 10**7, "repeat_last_n")
        for key in ["temperature", "top_p", "min_p", "repeat_penalty", "presence_penalty", "frequency_penalty"]:
            require(type(options[key]) in (int, float), "Invalid sampling number: " + key)
        require(options["temperature"] >= 0 and options["repeat_penalty"] > 0, "Invalid sampling range")
        require(0 <= options["top_p"] <= 1 and 0 <= options["min_p"] <= 1, "Invalid probability")

    @classmethod
    def compile_graph(cls, d, registry, settings):
        segments = []
        known = {}
        for row in d["segments"]:
            require(set(row) == {"id", "parent", "start", "stop", "history"}, "Invalid segment fields")
            name = identifier(row["id"])
            require(name not in known, "Duplicate segment")
            start = integer(row["start"], 1, 99, "segment start")
            stop = integer(row["stop"], start, 99, "segment stop")
            parent = row["parent"]
            require((parent is None and not segments and start == 1) or
                    (parent in known and start == known[parent].stop + 1),
                    "Segment must extend its actual parent without a gap")
            require(row["history"] in ("F", "R"), "Unknown history policy")
            segment = Segment(name, parent, start, stop, row["history"])
            segments.append(segment)
            known[name] = segment
        require(segments, "No segments")
        roots = []
        coordinates = set()
        pairings = {}
        labels = {m.label for m in registry.models}
        for row in d["roots"]:
            require(set(row) == {"id", "pairing_index", "root_index", "X", "Y", "segment_order"}, "Invalid root fields")
            name = identifier(row["id"])
            pair = integer(row["pairing_index"], 1, 99, "pairing index")
            number = integer(row["root_index"], 1, 99, "root index")
            require(row["X"] in labels and row["Y"] in labels, "Unknown participant model")
            require((pair, number) not in coordinates, "Repeated seed coordinates")
            coordinates.add((pair, number))
            require(pair not in pairings or pairings[pair] == (row["X"], row["Y"]), "Inconsistent pairing index")
            pairings[pair] = (row["X"], row["Y"])
            order = tuple(row["segment_order"])
            require(len(order) == len(known) and set(order) == set(known), "Invalid segment schedule")
            completed = set()
            for segment_id in order:
                parent = known[segment_id].parent
                require(parent is None or parent in completed, "Child scheduled before parent")
                completed.add(segment_id)
            roots.append(Root(name, pair, number, row["X"], row["Y"], order))
        require(roots and len({r.name for r in roots}) == len(roots), "Duplicate/empty roots")
        result = cls(canonical(d), registry.digest, d["system_prompt"], d["opening_X"],
                     canonical(settings), d["recent_messages"], d["seed_base"], tuple(roots), tuple(segments))
        require(all(n.seed < 2**31 for n in result.nodes()), "Seed exceeds supported integer range")
        return result

    @classmethod
    def load(cls, path, registry):
        return cls.from_dict(read_json(Path(path).read_text()), registry)

    @property
    def digest(self):
        return fingerprint(read_json(self.document_json))

    def nodes(self):
        segments = {s.name: s for s in self.segments}
        result = []
        for root in self.roots:
            for segment_id in root.order:
                segment = segments[segment_id]
                for turn in range(segment.start, segment.stop + 1):
                    if turn > segment.start:
                        parent = f"{root.name}:{segment_id}:{turn-1}"
                    elif segment.parent is not None:
                        parent = f"{root.name}:{segment.parent}:{segments[segment.parent].stop}"
                    else:
                        parent = None
                    speaker = "X" if turn % 2 else "Y"
                    seed = (self.seed_base + 1000000 * root.pairing_index + 10000 * root.root_index
                            + 1000 * (1 if speaker == "X" else 2) + 10 * turn)
                    result.append(Node(f"{root.name}:{segment_id}:{turn}", root.name, segment_id,
                                       turn, speaker, root.x_model if speaker == "X" else root.y_model,
                                       parent, segment.history, seed))
        return tuple(result)
