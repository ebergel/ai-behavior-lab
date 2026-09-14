"""Command-line access to the first laboratory milestone."""

import argparse
import json
from pathlib import Path
import sys

from .journal import Journal, rebuild_index
from .legacy import import_corpus, corpus_summary, reindex_corpus, verify_corpus
from .protocol import Protocol, Registry
from .runner import NeedsAttention, create_campaign, execute, summarize


def main(argv=None):
    parser = argparse.ArgumentParser(prog="behaviorlab", description="Independent behavior laboratory; Milestone 1 uses synthetic inference only.")
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
            result = {"valid": True, "execution_class": "engineering_fake_only", "planned_nodes": len(protocol.nodes()),
                      "roots": len(protocol.roots), "protocol_sha256": protocol.digest, "registry_sha256": registry.digest}
        elif args.command == "demo":
            directory = Path(args.directory)
            if bool(args.protocol) != bool(args.registry):
                parser.error("Supply --protocol and --registry together")
            if not directory.exists():
                if not args.protocol:
                    parser.error("A new campaign requires --protocol and --registry")
                registry = Registry.load(args.registry)
                protocol = Protocol.load(args.protocol, registry)
                create_campaign(directory, protocol, registry)
            elif args.protocol:
                registry = Registry.load(args.registry)
                protocol = Protocol.load(args.protocol, registry)
                saved = summarize(directory)
                if saved["protocol_sha256"] != protocol.digest or saved["registry_sha256"] != registry.digest:
                    raise ValueError("Supplied documents differ from the frozen campaign")
            result = execute(directory, max_calls=args.max_calls, retry_unresolved=args.retry_unresolved)
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
