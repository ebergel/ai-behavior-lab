"""Command-line access to the laboratory and its local WebUI integration."""

import argparse
import json
import os
from pathlib import Path
import sys

from .journal import Journal, rebuild_index
from .legacy import import_corpus, corpus_summary, reindex_corpus, verify_corpus
from .protocol import Protocol, Registry
from .runner import NeedsAttention, create_campaign, execute, summarize
from .common import read_json, require
from .webui import login_local, catalog, export_transcript, import_transcript


def main(argv=None):
    parser = argparse.ArgumentParser(prog="behaviorlab", description="Independent behavior laboratory: synthetic and bounded local engineering campaigns.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate a protocol and pinned registry")
    validate.add_argument("--protocol", required=True)
    validate.add_argument("--registry", required=True)
    demo = sub.add_parser("demo", help="create or resume a SYNTHETIC campaign, without contacting a model")
    demo.add_argument("directory")
    demo.add_argument("--protocol", help="required for a new campaign; checked against an existing snapshot if supplied")
    demo.add_argument("--registry", help="required with --protocol")
    demo.add_argument("--max-calls", type=int)
    demo.add_argument("--retry-unresolved", action="store_true", help="explicitly authorize a new attempt after a saved error/unknown outcome")
    live = sub.add_parser("run-local", help="create/resume a local engineering protocol; makes real model calls")
    live.add_argument("directory")
    live.add_argument("--protocol")
    live.add_argument("--registry")
    live.add_argument("--max-calls", type=int, required=True, help="maximum NEW generation attempts in this invocation")
    live.add_argument("--request-timeout", type=float, default=120,
                      help="generation HTTP timeout in seconds; client control, not a model parameter")
    live.add_argument("--retry-unresolved", action="store_true")
    live.add_argument("--webui-token-file", help="private session file; contents never enter the evidence journal")
    for command in ("webui-login", "webui-models", "webui-import"):
        p = sub.add_parser(command)
        p.add_argument("--endpoint", default="http://127.0.0.1:8080")
        p.add_argument("--token-file", default="workspace/private/webui-token")
        if command == "webui-import":
            p.add_argument("document")
            p.add_argument("--receipt", required=True)
    export = sub.add_parser("webui-export", help="export one actual ancestry as a display-only WebUI transcript")
    export.add_argument("directory")
    export.add_argument("leaf")
    export.add_argument("output")
    for command in ["status", "reindex"]:
        sub.add_parser(command).add_argument("directory")
    inspect = sub.add_parser("inspect", help="show a node's exact requests, responses, and outcome")
    inspect.add_argument("directory")
    inspect.add_argument("node_id")
    legacy = sub.add_parser("import-legacy", help="copy a reference corpus into its own evidence store")
    legacy.add_argument("--source", required=True)
    legacy.add_argument("--destination", required=True)
    legacy.add_argument("--source-url", required=True)
    legacy.add_argument("--revision")
    legacy.add_argument("--audit")
    legacy.add_argument("--expected-runs", type=int)
    for command in ["legacy-status", "legacy-reindex", "legacy-verify"]:
        sub.add_parser(command).add_argument("directory")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            registry = Registry.load(args.registry)
            protocol = Protocol.load(args.protocol, registry)
            result = {"valid": True, "execution_class": read_json(protocol.document_json)["execution_class"], "planned_nodes": len(protocol.nodes()),
                      "roots": len(protocol.roots), "protocol_sha256": protocol.digest, "registry_sha256": registry.digest}
        elif args.command in ("demo", "run-local"):
            expected = "engineering_local" if args.command == "run-local" else "engineering_fake_only"
            if args.command == "run-local" and args.webui_token_file:
                os.environ["BEHAVIORLAB_WEBUI_TOKEN"] = Path(args.webui_token_file).read_text().strip()
            directory = Path(args.directory)
            if bool(args.protocol) != bool(args.registry):
                parser.error("Supply --protocol and --registry together")
            if not directory.exists():
                if not args.protocol:
                    parser.error("A new campaign requires --protocol and --registry")
                registry = Registry.load(args.registry)
                protocol = Protocol.load(args.protocol, registry)
                require(read_json(protocol.document_json)["execution_class"] == expected, "Wrong command for this execution class")
                create_campaign(directory, protocol, registry)
            elif args.protocol:
                registry = Registry.load(args.registry)
                protocol = Protocol.load(args.protocol, registry)
                saved = summarize(directory)
                if saved["protocol_sha256"] != protocol.digest or saved["registry_sha256"] != registry.digest:
                    raise ValueError("Supplied documents differ from the frozen campaign")
            from .journal import read_events
            existing = read_events(directory / "events.jsonl")
            require(existing[0]["payload"]["protocol"]["execution_class"] == expected, "Wrong command for this execution class")
            from .backends import HTTPBackend
            backend = HTTPBackend(request_timeout=args.request_timeout) if args.command == "run-local" else None
            result = execute(directory, backend=backend, max_calls=args.max_calls, retry_unresolved=args.retry_unresolved)
        elif args.command == "webui-login":
            result = login_local(args.endpoint, args.token_file)
        elif args.command == "webui-models":
            result = catalog(args.endpoint, Path(args.token_file).read_text().strip())
        elif args.command == "webui-export":
            document = export_transcript(args.directory, args.leaf)
            with Path(args.output).open("x") as f:
                json.dump(document, f, ensure_ascii=False, indent=2)
            result = {"exported": str(Path(args.output).resolve()), "display_only": True}
        elif args.command == "webui-import":
            result = import_transcript(args.endpoint, Path(args.token_file).read_text().strip(),
                                       read_json(Path(args.document).read_text()), args.receipt)
        elif args.command == "status":
            result = summarize(args.directory)
        elif args.command == "reindex":
            with Journal(args.directory) as journal:
                rebuild_index(args.directory, journal.events)
            result = summarize(args.directory)
        elif args.command == "inspect":
            with Journal(args.directory) as journal:
                result = [e for e in journal.events if e["payload"].get("node_id") == args.node_id]
        elif args.command == "import-legacy":
            result = import_corpus(args.source, args.destination, args.source_url, args.revision, args.audit, args.expected_runs)
        elif args.command == "legacy-reindex":
            reindex_corpus(args.directory)
            result = corpus_summary(args.directory)
        elif args.command == "legacy-verify":
            manifest = verify_corpus(args.directory)
            result = {"valid": True, "dataset_sha256": manifest["dataset_sha256"], "runs": len(manifest["runs"])}
        else:
            result = corpus_summary(args.directory)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, StopIteration, NeedsAttention) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
