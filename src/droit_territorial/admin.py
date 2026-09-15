"""Bounded operator import of the official administrative XML archives, with a local FTS index."""

import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath

from .archive import private_database
from .models import Document, LegalOrder, SourceError

ARCHIVE_URL = re.compile(
    r"https://opendata\.justice-administrative\.fr/(DCE|DCA|DTA)/(\d{4})/(\d{2})/"
    r"(CE|CAA|TA)_(\d{6})\.zip"
)


def parse_xml(raw, filename, url, official=False):
    if len(raw) > 2_000_000 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise SourceError("unsafe_xml", "XML entities, DTDs and oversized documents are refused")
    try:
        decoded = raw.decode("utf-8-sig")  # Reject alternative encodings hiding a DTD.
        root = ET.fromstring(decoded)

        def field(name):
            return (root.findtext(".//" + name) or "").strip()

        identifier = field("Identification")
        number, court = field("Numero_Dossier"), field("Code_Juridiction")
        when = date.fromisoformat(field("Date_Lecture"))
        body = root.find(".//Texte_Integral")
        text = "\n".join("".join(p.itertext()).strip() for p in body) if body is not None else ""
        if body is not None and not list(body):
            text = "".join(body.itertext()).strip()
        if root.tag != "Document" or identifier != filename or not number or not court or not text:
            raise ValueError("Incomplete official XML")
        level = (
            "CE"
            if court == "CE"
            else "CAA"
            if court.startswith("CAA")
            else "TA"
            if court.startswith("TA")
            else None
        )
        if not level:
            raise ValueError("Unknown jurisdiction")
        return Document(
            provider="admin",
            canonical_id=identifier,
            canonical_url=url,
            title=f"{level} {field('Nom_Juridiction')} — {number} — {when}",
            text=text,
            document_kind="case_law",
            legal_order=LegalOrder.ADMINISTRATIVE,
            court_or_issuer=court,
            decision_date=when,
            source_updated_at=field("Date_Mise_Jour") or None,
            original_content_hash=hashlib.sha256(raw).hexdigest(),
            ecli=field("Numero_ECLI") or None,
            decision_type=field("Type_Decision") or None,
            publication_code=field("Code_Publication") or None,
            source_authenticity="official" if official else "unknown",
            source_complete=True,
            reuse_policy="Licence Ouverte 2.0; respecter la pseudonymisation et les CGU du producteur",
            warnings=[
                "Imported subset only; publication date and current withdrawal status not established",
                "XML paragraphs preserved; party/judge attribution requires reading",
            ],
        ), level
    except (ET.ParseError, UnicodeError, ValueError) as exc:
        raise SourceError(
            "invalid_admin_xml", "Unrecognized or incomplete administrative XML"
        ) from exc


class AdminIndex:
    def __init__(self, path):
        self.path = path

    def connect(self, create=False):
        if not self.path or (not create and not Path(self.path).is_file()):
            raise SourceError(
                "admin_index_not_configured", "Import an official archive with --db first"
            )
        db = private_database(self.path)
        if create:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS batches(hash TEXT PRIMARY KEY, url TEXT, imported_at TEXT, count INTEGER);
                CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY, level TEXT, day TEXT,
                    body TEXT, xml BLOB, xml_hash TEXT, body_hash TEXT, batch_hash TEXT, withdrawn INTEGER DEFAULT 0);
                CREATE VIRTUAL TABLE IF NOT EXISTS decision_search USING fts5(id UNINDEXED, text,
                    tokenize='unicode61 remove_diacritics 2');
            """)
        return db

    async def sync(self, url, transport):
        match = ARCHIVE_URL.fullmatch(url)
        if (
            not match
            or {"DCE": "CE", "DCA": "CAA", "DTA": "TA"}[match[1]] != match[4]
            or match[2] + match[3] != match[5]
        ):
            raise SourceError(
                "invalid_archive_url", "Use an exact monthly ZIP link from the official portal"
            )
        raw = await transport.request("GET", url, provider="admin", max_bytes=64_000_000)
        return self._import_zip(raw, url, official=True)

    def _import_zip(self, raw, url, official=False):
        if len(raw) > 64_000_000:
            raise SourceError("archive_limit", "Compressed archive exceeds 64 MB")
        archive_hash = hashlib.sha256(raw).hexdigest()
        now = datetime.now(UTC).isoformat()
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                entries = archive.infolist()
                if (
                    not entries
                    or len(entries) > 15000
                    or sum(e.file_size for e in entries) > 200_000_000
                ):
                    raise SourceError(
                        "archive_limit", "Archive exceeds 15000 entries or 200 MB expanded"
                    )
                names = [PurePosixPath(e.filename).name for e in entries if not e.is_dir()]
                if len(set(names)) != len(names):
                    raise SourceError("invalid_archive", "Duplicate XML member")
                parsed = []
                for entry in entries:
                    path = PurePosixPath(entry.filename)
                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or len(path.parts) > 2
                        or "\\" in entry.filename
                    ):
                        raise SourceError("unsafe_archive", "Unsafe archive member path")
                    if entry.is_dir():
                        continue
                    if path.suffix != ".xml" or entry.file_size > 2_000_000:
                        raise SourceError("unsafe_archive", "Only bounded XML members are accepted")
                    xml = archive.read(entry)
                    doc, level = parse_xml(xml, path.name, url, official)
                    match = ARCHIVE_URL.fullmatch(url)
                    if official and (not match or match[4] != level):
                        raise SourceError(
                            "invalid_admin_xml", "Court differs from the official archive"
                        )
                    doc.retrieved_at = datetime.fromisoformat(now)
                    doc.collection_hash = archive_hash
                    body = doc.model_dump_json()
                    parsed.append(
                        (
                            doc.canonical_id,
                            level,
                            str(doc.decision_date),
                            body,
                            xml,
                            hashlib.sha256(xml).hexdigest(),
                            hashlib.sha256(body.encode()).hexdigest(),
                            archive_hash,
                        )
                    )
                if not parsed:
                    raise SourceError("invalid_archive", "Archive contains no decisions")
            with self.connect(create=True) as db:
                if db.execute("SELECT 1 FROM batches WHERE hash=?", (archive_hash,)).fetchone():
                    return {
                        "status": "already_imported",
                        "archive_hash": archive_hash,
                        "count": len(parsed),
                    }
                for row in parsed:
                    db.execute(
                        """INSERT INTO decisions(id,level,day,body,xml,xml_hash,body_hash,batch_hash)
                        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET level=excluded.level,
                        day=excluded.day,body=excluded.body,xml=excluded.xml,xml_hash=excluded.xml_hash,
                        body_hash=excluded.body_hash,batch_hash=excluded.batch_hash""",
                        row,
                    )
                    db.execute("DELETE FROM decision_search WHERE id=?", (row[0],))
                    doc = Document.model_validate_json(row[3])
                    db.execute(
                        "INSERT INTO decision_search VALUES(?,?)",
                        (row[0], doc.title + "\n" + doc.text),
                    )
                db.execute(
                    "INSERT INTO batches VALUES(?,?,?,?)", (archive_hash, url, now, len(parsed))
                )
            return {
                "status": "imported",
                "archive_hash": archive_hash,
                "url": url,
                "count": len(parsed),
                "imported_at": now,
            }
        except (zipfile.BadZipFile, RuntimeError) as exc:
            raise SourceError("invalid_archive", "ZIP decoding or integrity failed") from exc

    def coverage(self):
        with self.connect() as db:
            counts = db.execute(
                "SELECT level,COUNT(*),MIN(day),MAX(day) FROM decisions WHERE withdrawn=0 GROUP BY level"
            ).fetchall()
            batches = db.execute(
                "SELECT hash,url,imported_at,count FROM batches ORDER BY imported_at"
            ).fetchall()
        return {
            "scope": "Imported files only; no inference of national exhaustiveness",
            "courts": [
                {"level": x[0], "count": x[1], "earliest_decision": x[2], "latest_decision": x[3]}
                for x in counts
            ],
            "batches": [
                dict(zip(("hash", "url", "imported_at", "count"), x, strict=True)) for x in batches
            ],
            "withdrawal_sync": "manual; current provider withdrawals not automatically checked",
        }

    def search(self, query, courts=None, date_start=None, date_end=None, offset=0, blocked_ids=()):
        terms = re.findall(r"[^\W_]+", query, re.UNICODE)
        if not terms or len(query) > 1000 or len(terms) > 30 or not 0 <= offset <= 10000:
            raise SourceError(
                "invalid_input", "Use 1–30 words, <=1000 characters and a bounded offset"
            )
        courts = courts or ["CE", "CAA", "TA"]
        if set(courts) - {"CE", "CAA", "TA"} or (date_start and date_end and date_start > date_end):
            raise SourceError("invalid_input", "Invalid administrative court or date bounds")
        params = [" AND ".join('"' + x + '"' for x in terms), *courts]
        where = (
            "decision_search MATCH ? AND d.withdrawn=0 AND d.level IN ("
            + ",".join("?" for _ in courts)
            + ")"
        )
        for clause, value in (("d.day>=?", date_start), ("d.day<=?", date_end)):
            if value:
                where += " AND " + clause
                params.append(str(value))
        if blocked_ids:
            where += " AND d.id NOT IN (" + ",".join("?" for _ in blocked_ids) + ")"
            params.extend(blocked_ids)
        with self.connect() as db:
            rows = db.execute(
                "SELECT d.id,d.body FROM decision_search JOIN decisions d ON d.id=decision_search.id WHERE "
                + where
                + " ORDER BY d.day DESC,d.id LIMIT 21 OFFSET ?",
                [*params, offset],
            ).fetchall()
        return {
            "status": "ok",
            "results": [
                {"source_ref": "admin:" + row[0], "title": json.loads(row[1])["title"]}
                for row in rows[:20]
            ],
            "next_offset": offset + 20 if len(rows) > 20 else None,
            "coverage": self.coverage(),
            "search_semantics": "All words, accent-insensitive lexical match; no semantic search",
            "content_trust": "untrusted_data",
            "legal_validity": "not_assessed",
        }

    def fetch(self, identifier):
        with self.connect() as db:
            row = db.execute(
                "SELECT body,xml,xml_hash,body_hash FROM decisions WHERE id=? AND withdrawn=0",
                (identifier,),
            ).fetchone()
        if row is None:
            raise SourceError(
                "reference_unavailable", "Decision unavailable in the imported corpus"
            )
        if (
            not isinstance(row[1], bytes)
            or hashlib.sha256(row[1]).hexdigest() != row[2]
            or hashlib.sha256(row[0].encode()).hexdigest() != row[3]
        ):
            raise SourceError("archive_corrupted", "Administrative source integrity check failed")
        doc = Document.model_validate_json(row[0])
        if doc.canonical_id != identifier:
            raise SourceError("archive_corrupted", "Administrative identity mismatch")
        return doc

    def withdraw(self, identifier):
        with self.connect() as db:
            db.execute("UPDATE decisions SET withdrawn=1 WHERE id=?", (identifier,))
