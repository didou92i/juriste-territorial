"""Transport-independent legal operations, with partial failures and immutable evidence."""

import asyncio
import difflib
import hashlib
import json
import time
import uuid
from collections import OrderedDict
from datetime import UTC, datetime

from .admin import AdminIndex
from .archive import Archive
from .dossier import Dossier, review
from .evidence import EvidenceStore
from .local import LocalReader
from .models import ClaimInput, LegalOrder, SourceError
from .resources import data_path
from .runtime import Settings, Transport
from .setup import setup_status
from .sources import OfficialSources


class Service:
    def __init__(self, settings: Settings | None = None, transport: Transport | None = None):
        self.settings = settings or Settings.from_env()
        self.transport = transport or Transport(self.settings)
        self.sources = OfficialSources(self.transport)
        self.local = LocalReader(self.settings.local_db, self.settings.principal)
        self.admin = AdminIndex(self.settings.admin_db)
        self.archive = (
            Archive(self.settings.evidence_db, self.settings.principal)
            if self.settings.evidence_db
            else None
        )
        self.evidence = EvidenceStore(archive=self.archive)
        self.cursors = OrderedDict()
        self.last_attempts = {}

    async def close(self):
        await self.transport.close()

    def source_status(self, source_id: str | None = None):
        rows = json.loads((data_path("registry") / "sources.json").read_text())
        if source_id and not any(r["id"] == source_id for r in rows):
            raise SourceError("unknown_source", "Unknown source id")
        for row in rows:
            if row["id"] == "legifrance":
                row["access_state"] = (
                    "configured_not_probed"
                    if self.settings.oauth_configured
                    else "credentials_missing"
                )
            elif row["id"] == "judilibre":
                row["access_state"] = (
                    "configured_not_probed"
                    if self.settings.oauth_configured or self.settings.judilibre_key
                    else "credentials_missing"
                )
            elif row["id"] == "local":
                row["access_state"] = (
                    "configured_not_probed"
                    if self.settings.local_db and self.settings.principal
                    else "not_configured"
                )
            elif row["id"] == "administrative_open_data":
                try:
                    row["imported_coverage"] = self.admin.coverage()
                    row["access_state"] = "imported_subset_available"
                except SourceError as exc:
                    row["access_state"] = exc.problem.code
            else:
                row["access_state"] = "browser_or_page_reader_only"
            row["last_attempt"] = self.last_attempts.get(row["id"])
            row["last_collection"] = None
            if row.get("imported_coverage", {}).get("batches"):
                row["last_collection"] = row["imported_coverage"]["batches"][-1]["imported_at"]
            row["software_version"] = "0.3.1"
        return {
            "status": "ok",
            "evidence_storage": "private_persistent" if self.archive else "ephemeral",
            "setup": setup_status(self.settings),
            "sources": [r for r in rows if not source_id or r["id"] == source_id],
            "scope": "Configuration and observed operations, not a current uptime or legal freshness guarantee",
        }

    async def search(
        self,
        query: str,
        source_types=None,
        legal_order="administrative",
        as_of_date=None,
        cursor=None,
        *,
        courts=None,
        date_start=None,
        date_end=None,
    ):
        query = query.strip()
        if not query or len(query) > 1000:
            raise SourceError("invalid_input", "Query must contain 1 to 1000 characters")
        try:
            order = LegalOrder(legal_order)
        except ValueError:
            raise SourceError("invalid_input", "Unknown legal order") from None
        kinds = list(
            dict.fromkeys(
                source_types
                if source_types is not None
                else ["codes", "legislation", "jorf", "case_law"]
            )
        )
        if not kinds or set(kinds) - {
            "codes",
            "legislation",
            "jorf",
            "case_law",
            "constitutional_case_law",
        }:
            raise SourceError("unsupported_source_type", "Unknown or empty source types")
        if date_start and date_end and date_start > date_end:
            raise SourceError("invalid_input", "Date range is reversed")
        if courts and order != LegalOrder.JUDICIAL:
            raise SourceError(
                "unsupported_filter",
                "Court filtering is supported only by JudiLibre in this version",
            )
        if set(kinds) & {"codes", "legislation"} and as_of_date is None:
            raise SourceError("date_required", "Provide the date for consolidated legal texts")
        providers = [k for k in kinds if k != "case_law"]
        if "case_law" in kinds:
            if order in {LegalOrder.ADMINISTRATIVE, LegalOrder.ANY}:
                providers.append("administrative_case_law")
            if order in {LegalOrder.JUDICIAL, LegalOrder.ANY}:
                providers.append("judicial_case_law")
        signature = hashlib.sha256(
            json.dumps(
                [query, kinds, order, str(as_of_date), courts, str(date_start), str(date_end)]
            ).encode()
        ).hexdigest()
        offsets = {p: 0 if p == "judicial_case_law" else 1 for p in providers}
        if cursor:
            state = self.cursors.get(cursor)
            if not state or state[0] != signature or time.monotonic() - state[2] > 1800:
                raise SourceError("invalid_cursor", "Cursor expired or belongs to another search")
            offsets = state[1]

        async def run(kind, page):
            provider = "judilibre" if kind == "judicial_case_law" else "legifrance"
            try:
                if page > 100:
                    raise SourceError(
                        "pagination_limit", "Refine the query after 100 pages", provider
                    )
                if kind == "judicial_case_law":
                    result = await self.sources.judiciary_search(
                        query, page, courts=courts, date_start=date_start, date_end=date_end
                    )
                else:
                    kwargs = (
                        {"date_start": date_start, "date_end": date_end}
                        if kind.endswith("case_law")
                        else {}
                    )
                    result = await self.sources.legi_search(query, kind, as_of_date, page, **kwargs)
                self.last_attempts[provider] = {"at": datetime.now(UTC).isoformat(), "status": "ok"}
                return kind, page, result, None
            except SourceError as exc:
                self.last_attempts[provider] = {
                    "at": datetime.now(UTC).isoformat(),
                    "status": exc.problem.code,
                }
                return kind, page, None, exc.problem.model_dump()

        batches = await asyncio.gather(*(run(k, p) for k, p in offsets.items()))
        results, errors, coverage, following = {}, [], [], {}
        for kind, page, batch, error in batches:
            if error:
                errors.append({"source_type": kind, **error})
                continue
            coverage.append({"source_type": kind, "page": page, "scope": batch["coverage"]})
            for row in batch["results"]:
                if row["canonical_id"] not in self.settings.blocked_ids:
                    results[row["source_ref"]] = row
            if batch["has_more"]:
                following[kind] = page + 1
        next_cursor = None
        if following:
            next_cursor = uuid.uuid4().hex
            self.cursors[next_cursor] = (signature, following, time.monotonic())
            while len(self.cursors) > 256:
                self.cursors.popitem(last=False)
        return {
            "status": "error" if errors and not coverage else "partial" if errors else "ok",
            "results": list(results.values()),
            "errors": errors,
            "coverage": coverage,
            "next_cursor": next_cursor,
            "as_of_date": str(as_of_date) if as_of_date else None,
            "warnings": [
                "Discovery only; fetch decisive sources",
                "as_of_date filters consolidated texts, not the applicability of decisions or JORF",
                "Failed sources must be retried separately; pagination continues successful sources only",
            ],
            "content_trust": "untrusted_data",
        }

    def _check_snapshot_access(self, ev):
        if ev.document.canonical_id in self.settings.blocked_ids:
            raise SourceError("reference_unavailable", "Reference unavailable")
        if ev.document.provider == "admin":
            # Preserve older snapshots, but honor withdrawals from the current index.
            self.admin.fetch(ev.document.canonical_id)
        if ev.document.provider == "local":
            current = self.local.fetch(ev.document.canonical_id)
            if hashlib.sha256(current.text.encode()).hexdigest() != ev.content_hash:
                raise SourceError(
                    "source_changed", "The local source changed; fetch a new snapshot"
                )

    async def fetch(self, source_ref, as_of_date=None, offset=0, length=6000):
        if not 1 <= length <= 12000 or offset < 0 or len(source_ref) > 2500:
            raise SourceError("invalid_input", "Invalid reference, length or offset")
        provider, sep, identifier = source_ref.partition(":")
        if not sep or not identifier:
            raise SourceError(
                "invalid_reference",
                "Use a reference returned by search or an explicit supported provider reference",
            )
        if provider == "evidence":
            ev = self.evidence.get(identifier)
            self._check_snapshot_access(ev)
            if as_of_date and as_of_date != ev.as_of_date:
                raise SourceError("snapshot_date_mismatch", "Refetch the source for another date")
        else:
            if offset:
                raise SourceError(
                    "snapshot_required", "Use the returned evidence: reference for subsequent pages"
                )
            if identifier in self.settings.blocked_ids:
                raise SourceError("reference_unavailable", "Reference unavailable")
            if provider == "legifrance":
                doc = await self.sources.legi_fetch(identifier, as_of_date)
            elif provider == "judilibre":
                doc = await self.sources.judiciary_fetch(identifier)
            elif provider == "web":
                doc = await self.sources.official_page(identifier)
            elif provider == "local":
                doc = self.local.fetch(identifier)
            elif provider == "admin":
                doc = self.admin.fetch(identifier)
            else:
                raise SourceError(
                    "unsupported_source",
                    "Supported references: legifrance:, judilibre:, web:, local:, admin:, evidence:",
                )
            ev = self.evidence.put(source_ref, doc, as_of_date)
        return self.evidence.page(ev.evidence_id, offset, length)

    async def legal_version(self, text_ref, article, as_of_date):
        # text_ref is the exact code title, deliberately not an unverified arbitrary facet.
        if not text_ref.strip() or len(text_ref) > 300 or not article.strip() or len(article) > 50:
            raise SourceError("invalid_input", "Provide the exact code title and article number")
        compact = article.replace(" ", "").replace(".", "").upper()
        batch = await self.sources.legi_search(
            article, "codes", as_of_date, article=compact, code=text_ref
        )
        hits = [
            row
            for row in batch["results"]
            if row["article_number"].replace(" ", "").replace(".", "").upper() == compact
            and row["canonical_id"].startswith("LEGIARTI")
            and (row.get("code_title") or "").casefold() == text_ref.strip().casefold()
        ]
        if len(hits) != 1 or batch["has_more"]:
            return {
                "status": "version_unknown",
                "reason": "No unique complete article match at the requested date",
                "candidates": hits,
            }
        result = await self.fetch(hits[0]["source_ref"], as_of_date)
        if result["temporal_applicability"] != "yes":
            result["status"] = "version_unknown"
        return result

    async def compare_versions(self, text_ref, article, from_date, to_date):
        if from_date > to_date:
            raise SourceError("invalid_input", "Version comparison dates are reversed")
        before = await self.legal_version(text_ref, article, from_date)
        after = await self.legal_version(text_ref, article, to_date)
        if before["status"] != "ok" or after["status"] != "ok":
            return {"status": "version_unknown", "before": before, "after": after}
        old = self.evidence.get(before["evidence_id"]).document.text
        new = self.evidence.get(after["evidence_id"]).document.text
        diff = "\n".join(
            difflib.unified_diff(
                old.splitlines(),
                new.splitlines(),
                fromfile=from_date.isoformat(),
                tofile=to_date.isoformat(),
                lineterm="",
            )
        )
        return {
            "status": "ok",
            "before_evidence_id": before["evidence_id"],
            "after_evidence_id": after["evidence_id"],
            "changed": old != new,
            "diff": diff[:24000],
            "diff_complete": len(diff) <= 24000,
            "legal_effect": "not_assessed",
            "warning": "Read the amending text and transitional provisions",
        }

    async def resolve_references(self, source_ref, as_of_date, depth_limit=1):
        if not 1 <= depth_limit <= 2:
            raise SourceError("invalid_input", "Reference depth is limited to 1 or 2")
        queue, seen, resolved, unresolved = [(source_ref, 0)], set(), [], []
        while queue and len(seen) < 12:
            ref, depth = queue.pop(0)
            if ref in seen:
                continue
            seen.add(ref)
            try:
                result = await self.fetch(ref, as_of_date)
                resolved.append(result)
                ev = self.evidence.get(result["evidence_id"])
                for child in ev.document.related_refs:
                    if depth < depth_limit and child not in seen:
                        queue.append((child, depth + 1))
                    elif child not in seen:
                        unresolved.append({"source_ref": child, "reason": "depth_limit"})
            except SourceError as exc:
                unresolved.append({"source_ref": ref, "reason": exc.problem.code})
        unresolved += [
            {"source_ref": ref, "reason": "document_limit"} for ref, _ in queue if ref not in seen
        ]
        return {
            "status": "partial" if unresolved else "ok",
            "resolved": resolved,
            "unresolved": unresolved,
            "coverage": "Explicit canonical identifiers returned in links/text only; implicit legal references still require research",
        }

    def check_evidence(self, claims: list[ClaimInput]):
        if not 1 <= len(claims) <= 30:
            raise SourceError("invalid_input", "Check 1 to 30 claims at a time")
        results = []
        for claim in claims:
            try:
                self._check_snapshot_access(self.evidence.get(claim.evidence_id))
                results.append(self.evidence.check(claim))
            except SourceError as exc:
                results.append(
                    {
                        "claim_id": claim.claim_id,
                        "status": "error",
                        "error": exc.problem.model_dump(),
                    }
                )
        return {
            "status": "technical_check_only",
            "claims": results,
            "legal_validity": "not_assessed",
        }

    def review_case(self, dossier: Dossier):
        return review(dossier, self)

    def record_case(self, dossier: Dossier):
        if self.archive is None:
            raise SourceError("archive_not_configured", "Configure a private archive first")
        report = self.review_case(dossier)
        identifier = self.archive.put(
            "case",
            {
                "recorded_at": datetime.now(UTC).isoformat(),
                "dossier": dossier.model_dump(mode="json"),
                "report": report,
            },
        )
        return {"status": "recorded", "record_id": identifier, "report": report}

    def read_case(self, identifier):
        if self.archive is None:
            raise SourceError("archive_not_configured", "Configure a private archive first")
        record = self.archive.get("case", identifier)
        dossier = Dossier.model_validate(record["dossier"])
        # Do not re-expose withdrawn private excerpts preserved inside the historical note.
        for piece in dossier.pieces:
            self._check_snapshot_access(self.evidence.get(piece.evidence_id))
        return {
            "status": "historical_record",
            "record": record,
            "current_review": self.review_case(dossier),
            "legal_validity": "not_assessed",
        }

    def compare_evidence(self, before_id, after_id):
        old, new = self.evidence.get(before_id), self.evidence.get(after_id)
        for ev in (old, new):
            self._check_snapshot_access(ev)
        if (old.document.provider, old.document.canonical_id) != (
            new.document.provider,
            new.document.canonical_id,
        ):
            raise SourceError(
                "different_documents", "Compare snapshots of the same canonical document"
            )
        content_changed = old.content_hash != new.content_hash
        metadata_changed = old.document.model_dump(
            exclude={"text", "retrieved_at"}
        ) != new.document.model_dump(exclude={"text", "retrieved_at"})
        return {
            "status": "technical_check_only",
            "before_id": before_id,
            "after_id": after_id,
            "content_changed": content_changed,
            "metadata_changed": metadata_changed,
            "reexamination_required": content_changed
            or metadata_changed
            or old.as_of_date != new.as_of_date,
            "legal_effect": "not_assessed",
            "historical_record_modified": False,
        }
