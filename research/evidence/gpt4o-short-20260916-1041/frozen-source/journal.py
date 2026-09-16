"""Single-writer, append-only evidence journal with a rebuildable SQLite index."""

import fcntl
import os
from pathlib import Path
import sqlite3
import tempfile

from .common import canonical, fingerprint, read_json, require, timestamp


def read_events(path):
    data = Path(path).read_bytes()
    require(not data or data.endswith(b"\n"),
            "Incomplete journal tail: preserve the file for recovery; no automatic truncation")
    result = []
    previous = "0" * 64
    for line in data.split(b"\n")[:-1]:
        event = read_json(line.decode("utf-8"))
        require(set(event) == {"schema", "seq", "at", "kind", "payload", "previous", "hash"}, "Invalid event envelope")
        require(event["schema"] == "behaviorlab.event/1", "Unknown journal version")
        require(event["seq"] == len(result) + 1 and event["previous"] == previous, "Broken journal sequence")
        body = {k: v for k, v in event.items() if k != "hash"}
        require(event["hash"] == fingerprint(body), "Journal content checksum mismatch")
        require(isinstance(event["kind"], str) and isinstance(event["payload"], dict), "Invalid event type/payload")
        result.append(event)
        previous = event["hash"]
    return result


class Journal:
    def __init__(self, directory, create=False):
        self.directory = Path(directory)
        self.path = self.directory / "events.jsonl"
        self.create = create
        self.events = []
        self.lock = None
        self.output = None

    def __enter__(self):
        self.lock = (self.directory / "writer.lock").open("a+b")
        try:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.create:
                self.path.open("xb").close()
            self.events = read_events(self.path)
            self.output = self.path.open("ab")
            return self
        except BaseException:
            self.lock.close()
            raise

    def __exit__(self, *exc):
        if self.output:
            self.output.close()
        if self.lock:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
            self.lock.close()

    def append(self, kind, payload):
        require(self.output is not None and not self.output.closed, "Journal is not open for writing")
        event = {"schema": "behaviorlab.event/1", "seq": len(self.events) + 1,
                 "at": timestamp(), "kind": kind, "payload": payload,
                 "previous": self.events[-1]["hash"] if self.events else "0" * 64}
        event["hash"] = fingerprint(event)
        # Round-trip before retaining the event, preventing mutation through caller aliases.
        line = canonical(event).encode("utf-8")
        self.output.write(line + b"\n")
        self.output.flush()
        os.fsync(self.output.fileno())
        saved = read_json(line.decode("utf-8"))
        self.events.append(saved)
        return saved


def rebuild_index(directory, events):
    """Rebuild from an already verified snapshot, normally while holding its writer lock."""
    directory = Path(directory)
    fd, temporary = tempfile.mkstemp(prefix="index-", suffix=".sqlite", dir=directory)
    os.close(fd)
    try:
        db = sqlite3.connect(temporary)
        try:
            db.executescript("""
                CREATE TABLE events (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL,
                    node_id TEXT, attempt_id TEXT, at TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE INDEX events_node ON events(node_id);
                CREATE TABLE identity (journal_events INTEGER, journal_head TEXT);
            """)
            with db:
                for event in events:
                    p = event["payload"]
                    db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (event["seq"], event["kind"],
                               p.get("node_id"), p.get("attempt_id"), event["at"], canonical(p)))
                db.execute("INSERT INTO identity VALUES (?,?)", (len(events), events[-1]["hash"] if events else None))
        finally:
            db.close()
        os.replace(temporary, directory / "index.sqlite")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
