"""Opt-in real PISTE probes; preserve each outcome and never translate failures to zero hits."""

import asyncio
import json
import uuid
from datetime import UTC, date, datetime

from droit_territorial.models import SourceError
from droit_territorial.service import Service


async def qualify(service):
    results = []
    for name, when in (
        ("historical_article", date(2026, 3, 31)),
        ("current_article", date(2026, 9, 15)),
    ):
        if not service.settings.oauth_configured:
            results.append({"probe": name, "status": "not_run", "reason": "credentials_missing"})
            continue
        try:
            answer = await service.legal_version("Code de la commande publique", "R2122-8", when)
            row = {"probe": name, "status": answer["status"], "as_of_date": str(when)}
            if answer.get("evidence_id"):
                ev = service.evidence.get(answer["evidence_id"])
                pages = 1
                while answer.get("next_offset") is not None:
                    answer = await service.fetch(
                        "evidence:" + ev.evidence_id, offset=answer["next_offset"]
                    )
                    pages += 1
                row.update(
                    canonical_id=ev.document.canonical_id,
                    content_hash=ev.content_hash,
                    temporal_applicability=ev.document.version.at(when),
                    pages_read=pages,
                    source_complete=ev.document.source_complete,
                )
            results.append(row)
        except SourceError as exc:
            results.append({"probe": name, "status": "error", "code": exc.problem.code})
    query = "jt_probe_absence_" + uuid.uuid4().hex
    if service.settings.oauth_configured:
        try:
            answer = await service.search(query, ["case_law"], "administrative")
            results.append(
                {
                    "probe": "unlikely_query",
                    "query": query,
                    "status": answer["status"],
                    "count": len(answer["results"]),
                    "errors": answer["errors"],
                    "meaning": "Observed query result only; no claim that law or case law does not exist",
                }
            )
        except SourceError as exc:
            results.append({"probe": "unlikely_query", "status": "error", "code": exc.problem.code})
    else:
        results.append(
            {"probe": "unlikely_query", "status": "not_run", "reason": "credentials_missing"}
        )
    return {
        "at": datetime.now(UTC).isoformat(),
        "piste_environment": "sandbox" if service.settings.sandbox else "production",
        "probes": results,
        "outage_handling": "simulated_tests_only",
        "legal_validation": "not_assessed",
    }


async def main():
    service = Service()
    try:
        print(json.dumps(await qualify(service), ensure_ascii=False, indent=2))
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
