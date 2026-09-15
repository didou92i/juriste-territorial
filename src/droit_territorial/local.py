"""Operator-managed local documents. Every lookup applies the principal before returning data."""

import hashlib
import re
import sqlite3
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .models import Document, SourceError

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
 id TEXT PRIMARY KEY, principal TEXT NOT NULL, case_id TEXT NOT NULL,
 title TEXT NOT NULL, text TEXT NOT NULL, search_text TEXT NOT NULL,
 original BLOB NOT NULL, original_hash TEXT NOT NULL, imported_at TEXT NOT NULL,
 withdrawn INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS document_access ON documents(principal,case_id,withdrawn);
"""


def lexical(value):
    return "".join(
        c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c)
    )


def import_document(db: Path, file: Path, principal: str, case_id: str, title: str):
    if file.suffix.lower() not in {".txt", ".md"}:
        raise ValueError(
            "Pilot imports UTF-8 .txt/.md only; PDF/OCR extraction must be reviewed first"
        )
    if not principal.strip() or not case_id.strip() or not title.strip():
        raise ValueError("Principal, case id and title are required")
    if file.stat().st_size > 2_000_000:
        raise ValueError("Document exceeds the 2 MB import limit")
    raw = file.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("Document exceeds the import limit")
    body = raw.decode("utf-8")
    if not body.strip():
        raise ValueError("Document is empty")
    db.parent.mkdir(parents=True, exist_ok=True)
    identifier = uuid.uuid4().hex
    with sqlite3.connect(db) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,0)",
            (
                identifier,
                principal,
                case_id,
                title,
                body,
                lexical(title + "\n" + body),
                raw,
                hashlib.sha256(raw).hexdigest(),
                datetime.now(UTC).isoformat(),
            ),
        )
    db.chmod(0o600)
    return identifier


def withdraw_document(db: Path, principal: str, identifier: str):
    # Write access belongs to the operator CLI; never exposed as an MCP tool.
    with sqlite3.connect(db) as connection:
        connection.execute(
            "UPDATE documents SET withdrawn=1 WHERE id=? AND principal=?", (identifier, principal)
        )


class LocalReader:
    def __init__(self, db: str, principal: str):
        self.db = Path(db).expanduser().resolve() if db else None
        self.principal = principal

    def _connect(self):
        if not self.db or not self.principal or not self.db.is_file():
            raise SourceError(
                "local_not_configured",
                "Operator must configure a local store and trusted principal",
                "local",
            )
        try:
            connection = sqlite3.connect(self.db.as_uri() + "?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as exc:
            raise SourceError("local_unavailable", "Local store unavailable", "local") from exc

    def search(self, query: str, case_id: str, offset=0, size=10):
        tokens = re.findall(r"\w+", lexical(query))[:20]
        if not tokens:
            raise SourceError("invalid_input", "A lexical search term is required")
        sql = "SELECT id,title,case_id,imported_at FROM documents WHERE principal=? AND case_id=? AND withdrawn=0"
        sql += " AND instr(search_text,?)>0" * len(tokens)
        sql += " ORDER BY imported_at,id LIMIT ? OFFSET ?"
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    sql, (self.principal, case_id, *tokens, size + 1, offset)
                ).fetchall()
        except sqlite3.Error as exc:
            raise SourceError(
                "local_unavailable", "Local store schema or query unavailable", "local"
            ) from exc
        return {
            "status": "ok",
            "results": [
                {
                    "source_ref": "local:" + row["id"],
                    "title": row["title"],
                    "case_id": row["case_id"],
                    "imported_at": row["imported_at"],
                    "evidence_status": "discovery_only",
                }
                for row in rows[:size]
            ],
            "next_offset": offset + size if len(rows) > size else None,
            "coverage": "Only authorized imported text documents; no presumption of legality or exhaustiveness",
        }

    def fetch(self, identifier):
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM documents WHERE id=? AND principal=? AND withdrawn=0",
                    (identifier, self.principal),
                ).fetchone()
        except sqlite3.Error as exc:
            raise SourceError("local_unavailable", "Local store unavailable", "local") from exc
        # Identical error for unknown, withdrawn and unauthorized identifiers.
        if row is None:
            raise SourceError("reference_unavailable", "Reference unavailable")
        if hashlib.sha256(row["original"]).hexdigest() != row["original_hash"]:
            raise SourceError(
                "integrity_error", "Stored original no longer matches its hash", "local"
            )
        if row["original"].decode("utf-8") != row["text"]:
            raise SourceError(
                "integrity_error", "Stored extraction differs from the imported original", "local"
            )
        return Document(
            provider="local",
            canonical_id=row["id"],
            title=row["title"],
            text=row["text"],
            document_kind="local_act",
            source_authenticity="unknown",
            source_complete=True,
            access_scope="private",
            case_id=row["case_id"],
            source_updated_at=row["imported_at"],
            withdrawal_status="not_reported",
            warnings=[
                "Imported document: authenticity, formalities, local scope and legal validity require analysis"
            ],
        )
