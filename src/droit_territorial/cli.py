import argparse
import asyncio
import json
from pathlib import Path

from .local import import_document, withdraw_document
from .resources import methodology
from .runtime import Settings
from .server import build_server
from .service import Service


def main():
    parser = argparse.ArgumentParser(prog="droit-territorial")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Run the read-only MCP")
    serve.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    serve.add_argument("--port", type=int, default=8765)
    commands.add_parser(
        "status", help="Show capabilities and configuration without exposing secrets"
    )
    method = commands.add_parser("methodology")
    method.add_argument("topic", nargs="?", default="core")
    ingest = commands.add_parser(
        "import-local", help="Operator-only import of a private text document"
    )
    ingest.add_argument("file", type=Path)
    for arg in ("db", "principal", "case", "title"):
        ingest.add_argument("--" + arg, required=True)
    withdraw = commands.add_parser(
        "withdraw-local", help="Operator-only withdrawal from search and evidence"
    )
    for arg in ("db", "principal", "id"):
        withdraw.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    if args.command == "serve":
        settings = Settings.from_env()
        if args.transport == "streamable-http":
            # Pilot HTTP is loopback only. Private documents require isolated stdio processes.
            settings.local_db = ""
            settings.principal = ""
            if not 1024 <= args.port <= 65535:
                parser.error("Choose an unprivileged port (1024–65535)")
        server = build_server(Service(settings))
        if args.transport == "stdio":
            server.run()
        else:
            server.run(transport="streamable-http", host="127.0.0.1", port=args.port)
    elif args.command == "status":

        async def status():
            service = Service()
            try:
                print(json.dumps(service.source_status(), ensure_ascii=False, indent=2))
            finally:
                await service.close()

        asyncio.run(status())
    elif args.command == "methodology":
        print(methodology(args.topic)["text"])
    elif args.command == "import-local":
        identifier = import_document(
            Path(args.db), args.file, args.principal, args.case, args.title
        )
        print(json.dumps({"source_ref": "local:" + identifier, "case_id": args.case}))
    elif args.command == "withdraw-local":
        withdraw_document(Path(args.db), args.principal, args.id)
        print(
            json.dumps(
                {"status": "processed", "detail": "Unavailable identifiers disclose no existence"}
            )
        )


if __name__ == "__main__":
    main()
