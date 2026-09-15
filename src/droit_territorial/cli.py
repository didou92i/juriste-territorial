import argparse
import asyncio
import json
from pathlib import Path

from .credentials import configure
from .dossier import Dossier
from .local import import_document, withdraw_document
from .models import SourceError
from .resources import methodology
from .runtime import Settings
from .server import build_server
from .service import Service
from .setup import probe_connection


def main():
    parser = argparse.ArgumentParser(prog="droit-territorial")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Run the read-only MCP")
    serve.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    serve.add_argument("--port", type=int, default=8765)
    commands.add_parser(
        "status", help="Show capabilities and configuration without exposing secrets"
    )
    setup = commands.add_parser(
        "configure", help="Store credentials in the OS keyring (hidden local input)"
    )
    setup.add_argument("provider", choices=["piste", "judilibre"])
    setup.add_argument("--environment", choices=["production", "sandbox"], default="production")
    doctor = commands.add_parser("doctor", help="Safe setup report; opt-in real API diagnosis")
    doctor.add_argument(
        "--probe", action="store_true", help="Run one public search and fetch (provider quota)"
    )
    doctor.add_argument("--source", choices=["legifrance", "judilibre"], default="legifrance")
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
    for command in ("review-case", "record-case"):
        commands.add_parser(command).add_argument("file", type=Path)
    commands.add_parser("read-case").add_argument("id")
    commands.add_parser("case-schema")
    admin = commands.add_parser("import-admin", help="Download and index one official monthly ZIP")
    admin.add_argument("url")
    admin.add_argument("--db", required=True)
    admin_withdraw = commands.add_parser("withdraw-admin")
    admin_withdraw.add_argument("id")
    admin_withdraw.add_argument("--db", required=True)
    args = parser.parse_args()
    if args.command == "configure":
        try:
            print(
                json.dumps(configure(args.provider, args.environment), ensure_ascii=False, indent=2)
            )
        except SourceError as exc:
            print(
                json.dumps(
                    {"status": "error", "error": exc.problem.model_dump()}, ensure_ascii=False
                )
            )
            raise SystemExit(1) from None
    elif args.command == "serve":
        settings = Settings.from_env()
        if args.transport == "streamable-http":
            # Pilot HTTP is loopback only. Private documents require isolated stdio processes.
            settings.local_db = ""
            settings.evidence_db = ""
            settings.admin_db = ""
            settings.principal = ""
            if not 1024 <= args.port <= 65535:
                parser.error("Choose an unprivileged port (1024–65535)")
        server = build_server(Service(settings))
        if args.transport == "stdio":
            server.run()
        else:
            server.run(transport="streamable-http", host="127.0.0.1", port=args.port)
    elif args.command in {"status", "doctor"}:

        async def status():
            service = Service()
            try:
                value = service.source_status()
                failed = False
                if args.command == "doctor" and args.probe:
                    value["connection_test"] = await probe_connection(service, args.source)
                    failed = value["connection_test"]["state"] != "verified_search_and_fetch"
                print(json.dumps(value, ensure_ascii=False, indent=2))
                if failed:
                    raise SystemExit(1)
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
    elif args.command == "case-schema":
        print(json.dumps(Dossier.model_json_schema(), ensure_ascii=False, indent=2))
    elif args.command in {
        "review-case",
        "record-case",
        "read-case",
        "import-admin",
        "withdraw-admin",
    }:

        async def operate():
            settings = Settings.from_env()
            if args.command in {"import-admin", "withdraw-admin"}:
                settings.admin_db = args.db
            service = Service(settings)
            try:
                if args.command == "import-admin":
                    value = await service.admin.sync(args.url, service.transport)
                elif args.command == "withdraw-admin":
                    service.admin.withdraw(args.id)
                    value = {"status": "processed"}
                elif args.command == "read-case":
                    value = service.read_case(args.id)
                else:
                    if args.file.stat().st_size > 4_000_000:
                        raise SourceError("document_too_large", "Dossier exceeds 4 MB")
                    dossier = Dossier.model_validate_json(args.file.read_bytes())
                    value = (
                        service.record_case(dossier)
                        if args.command == "record-case"
                        else service.review_case(dossier)
                    )
                print(json.dumps(value, ensure_ascii=False, indent=2))
            except SourceError as exc:
                print(json.dumps({"status": "error", "error": exc.problem.model_dump()}))
                raise SystemExit(1) from None
            finally:
                await service.close()

        asyncio.run(operate())


if __name__ == "__main__":
    main()
