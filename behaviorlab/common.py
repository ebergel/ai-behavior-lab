"""Stable serialization used for protocol identity and evidence integrity."""

import hashlib
import json
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return sha256(canonical(value).encode("utf-8"))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError("Non-finite JSON constant: " + value)


def read_json(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")
