"""Explicit import of the reference corpus; original bytes remain authoritative.

No historical model digest, request, or missing trace is inferred from the new
laboratory's registry. Audit notes are a separate, attributed analysis artifact.
"""

from collections import Counter
import os
from pathlib import Path
import sqlite3
import tempfile

from .common import canonical, fingerprint, read_json, require, sha256, timestamp


def parse_run(raw):
    rows = [(number, read_json(line.decode("utf-8")))
            for number, line in enumerate(raw.split(b"\n"), 1) if line.strip()]
    require(len(rows) >= 2, "Run lacks header/footer")
    header, footer = rows[0][1], rows[-1][1]
    require(header.get("kind") == "header" and footer.get("kind") == "footer", "Invalid legacy framing")
    require(sum(r.get("kind") == "header" for _, r in rows) == 1, "Duplicate legacy header")
    require(sum(r.get("kind") == "footer" for _, r in rows) == 1, "Duplicate legacy footer")
    messages = [r for _, r in rows if r.get("kind") == "message"]
    require(len(messages) == footer["pair_turns"], "Legacy footer/message-count mismatch")
    for turn, r in enumerate(messages, 1):
        require(r["turn"] == turn and r["speaker"] == ("X" if turn % 2 else "Y"), "Broken legacy turn sequence")
    for _, r in rows:
        require(isinstance(r, dict) and isinstance(r.get("kind"), str), "Unrecognized legacy record")
        for key in ("content", "thinking"):
            require(key not in r or r[key] is None or isinstance(r[key], str), "Invalid legacy text field")
    return rows


def discover(source):
    source = Path(source)
    found = []
    for stage, name in [(1, "runs"), (2, "runs2"), (3, "runs3")]:
        for path in sorted((source / "data" / name).glob("*_run*.jsonl")):
            found.append((stage, path, path.relative_to(source).as_posix()))
    require(found, "No reference runs found under data/runs, data/runs2, or data/runs3")
    return found


def import_corpus(source, destination, source_url, revision=None, audit=None, expected_runs=None):
    """The destination is new or an identical existing import; never overwrite evidence."""
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    require(source != destination and source not in destination.parents,
            "Import destination must be outside the reference repository")
    records = []
    blobs = {}
    for stage, path, relative in discover(source):
        raw = path.read_bytes()
        rows = parse_run(raw)
        counts = Counter(row["kind"] for _, row in rows)
        digest = sha256(raw)
        blobs[digest] = raw
        records.append({"source_path": relative, "stage": stage, "sha256": digest,
                        "bytes": len(raw), "records": len(rows), "pair_messages": counts["message"],
                        "third_messages": counts["third"]})
    if expected_runs is not None:
        require(len(records) == expected_runs, "Unexpected number of reference runs")
    supplements = []
    if audit:
        raw = Path(audit).read_bytes()
        digest = sha256(raw)
        blobs[digest] = raw
        supplements.append({"name": Path(audit).name, "sha256": digest, "bytes": len(raw),
                            "role": "separate_analysis_not_original_run_data"})
    identity = {"schema": "behaviorlab.legacy/1", "source_url": source_url,
                "source_revision": revision, "runs": records, "supplements": supplements}
    dataset_id = fingerprint(identity)
    manifest = dict(identity, dataset_sha256=dataset_id, imported_at=timestamp(),
                    provenance_note="Only source-recorded metadata is available; missing digests and requests remain unknown.")
    if destination.exists():
        saved = read_json((destination / "manifest.json").read_text())
        require(saved["dataset_sha256"] == dataset_id, "Destination contains a different dataset")
        verify_corpus(destination)
        return corpus_summary(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=destination.name + "-import-", dir=destination.parent))
    try:
        (staging / "blobs").mkdir()
        for digest, raw in blobs.items():
            with (staging / "blobs" / digest).open("xb") as output:
                output.write(raw)
        (staging / "manifest.json").write_text(canonical(manifest) + "\n")
        reindex_corpus(staging)
        # Rename fails if a nonempty destination was created concurrently.
        os.rename(staging, destination)
    except BaseException:
        # Preserve incomplete work for diagnosis; never erase imported source bytes.
        raise
    return corpus_summary(destination)


def verify_corpus(directory):
    directory = Path(directory)
    manifest = read_json((directory / "manifest.json").read_text())
    require(manifest["schema"] == "behaviorlab.legacy/1", "Unknown legacy manifest schema")
    identity = {k: manifest[k] for k in ["schema", "source_url", "source_revision", "runs", "supplements"]}
    require(fingerprint(identity) == manifest["dataset_sha256"], "Dataset manifest checksum mismatch")
    seen = set()
    for row in manifest["runs"] + manifest["supplements"]:
        digest = row["sha256"]
        require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "Invalid blob identity")
        if digest not in seen:
            raw = (directory / "blobs" / digest).read_bytes()
            require(len(raw) == row["bytes"] and sha256(raw) == digest, "Imported blob checksum mismatch")
            seen.add(digest)
    return manifest


def reindex_corpus(directory):
    directory = Path(directory)
    manifest = verify_corpus(directory)
    fd, temporary = tempfile.mkstemp(prefix="catalog-", suffix=".sqlite", dir=directory)
    os.close(fd)
    try:
        db = sqlite3.connect(temporary)
        try:
            db.executescript("""
                CREATE TABLE runs (source_path TEXT PRIMARY KEY, stage INTEGER, blob_sha256 TEXT,
                    condition TEXT, run_number INTEGER, model_tag TEXT, model_digest TEXT,
                    header_json TEXT NOT NULL, footer_json TEXT NOT NULL);
                CREATE TABLE records (source_path TEXT, line_number INTEGER, kind TEXT,
                    turn INTEGER, speaker TEXT, content TEXT, thinking TEXT, thinking_present INTEGER,
                    done_reason TEXT, record_json TEXT NOT NULL, PRIMARY KEY(source_path,line_number));
                CREATE INDEX record_kind ON records(kind);
                CREATE TABLE identity (dataset_sha256 TEXT);
            """)
            with db:
                db.execute("INSERT INTO identity VALUES (?)", (manifest["dataset_sha256"],))
                for item in manifest["runs"]:
                    rows = parse_run((directory / "blobs" / item["sha256"]).read_bytes())
                    h, f = rows[0][1], rows[-1][1]
                    counts = Counter(r["kind"] for _, r in rows)
                    require(len(rows) == item["records"] and counts["message"] == item["pair_messages"]
                            and counts["third"] == item["third_messages"], "Manifest counts do not match source")
                    db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?)", (item["source_path"], item["stage"],
                               item["sha256"], h.get("cond"), h.get("run"), h.get("pair_model"),
                               h.get("model_digest"), canonical(h), canonical(f)))
                    for line, row in rows:
                        db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?)", (item["source_path"], line,
                                   row["kind"], row.get("turn"), row.get("speaker"), row.get("content"),
                                   row.get("thinking"), int("thinking" in row), row.get("done_reason"), canonical(row)))
        finally:
            db.close()
        os.replace(temporary, directory / "catalog.sqlite")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def corpus_summary(directory):
    """Read the derived index and confirm it belongs to this manifest."""
    directory = Path(directory).resolve()
    manifest = read_json((directory / "manifest.json").read_text())
    db = sqlite3.connect((directory / "catalog.sqlite").as_uri() + "?mode=ro", uri=True)
    try:
        require(db.execute("SELECT dataset_sha256 FROM identity").fetchone()[0] == manifest["dataset_sha256"],
                "Stale corpus index; rebuild it")
        stages = []
        for stage, count in db.execute("SELECT stage,count(*) FROM runs GROUP BY stage ORDER BY stage"):
            counts = dict(db.execute("SELECT kind,count(*) FROM records JOIN runs USING(source_path) WHERE stage=? GROUP BY kind", (stage,)))
            stages.append({"stage": stage, "runs": count, "pair_messages": counts.get("message", 0),
                           "third_messages": counts.get("third", 0), "record_counts": counts})
        return {"data_class": "imported_reference_data", "dataset_sha256": manifest["dataset_sha256"],
                "source_url": manifest["source_url"], "source_revision": manifest["source_revision"],
                "runs": sum(s["runs"] for s in stages), "pair_messages": sum(s["pair_messages"] for s in stages),
                "third_messages": sum(s["third_messages"] for s in stages), "stages": stages,
                "known_model_digests": db.execute("SELECT count(*) FROM runs WHERE model_digest IS NOT NULL").fetchone()[0],
                "supplements": manifest["supplements"]}
    finally:
        db.close()
