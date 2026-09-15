"""Explicit live qualification of three small historical archives, never a national benchmark."""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime

from droit_territorial.models import ClaimInput
from droit_territorial.runtime import Settings
from droit_territorial.service import Service

LOTS = [
    ("CE", "https://opendata.justice-administrative.fr/DCE/2021/09/CE_202109.zip", "436740"),
    ("CAA", "https://opendata.justice-administrative.fr/DCA/2022/03/CAA_202203.zip", "20NT02444"),
    ("TA", "https://opendata.justice-administrative.fr/DTA/2022/06/TA_202206.zip", "1900103"),
]


async def probe(path):
    service = Service(Settings(admin_db=path))
    results = []
    try:
        for level, url, query in LOTS:
            imported = await service.admin.sync(url, service.transport)
            hits = service.admin.search(query, [level])
            if not hits["results"]:
                raise RuntimeError("Known sample decision not retrieved")
            fetched = await service.fetch(hits["results"][0]["source_ref"], length=1000)
            first = fetched
            text, pages = fetched["text"], 1
            while fetched["next_offset"] is not None:
                fetched = await service.fetch(
                    first["source_ref"], offset=fetched["next_offset"], length=1000
                )
                text += fetched["text"]
                pages += 1
            if hashlib.sha256(text.encode()).hexdigest() != first["content_hash"]:
                raise RuntimeError("Paginated text hash mismatch")
            check = service.check_evidence(
                [
                    ClaimInput(
                        claim_id="probe",
                        statement="Technical quote probe only",
                        evidence_id=first["evidence_id"],
                        quote=text[:100],
                    )
                ]
            )
            results.append(
                {
                    "level": level,
                    "import": imported,
                    "query": query,
                    "matched_ref": first["original_source_ref"],
                    "pages_read": pages,
                    "content_hash": first["content_hash"],
                    "original_xml_hash": first["metadata"]["original_content_hash"],
                    "quote_found": check["claims"][0]["quote_found"],
                    "legal_validity": check["legal_validity"],
                }
            )
        return {
            "at": datetime.now(UTC).isoformat(),
            "status": "sample_technical_chain_passed",
            "results": results,
            "coverage": service.admin.coverage(),
            "limits": "Three historical lots and three known-decision lookups; no recall, ranking, current-law or legal reasoning benchmark",
        }
    finally:
        await service.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(probe(args.db)), ensure_ascii=False, indent=2))
