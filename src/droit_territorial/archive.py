"""Optional operator-owned archive. Hashes detect corruption, not malicious administrator edits."""

import hashlib
import json
import os
import sqlite3
import stat
import uuid
from pathlib import Path

from .models import SourceError


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def private_database(path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(target, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise SourceError("unsafe_archive", "Archive must be a regular unlinked local file")
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)
    # Parent directory must remain under the trusted operator's control.
    return sqlite3.connect(target, factory=ClosingConnection)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Archive:
    def __init__(self, path: str, principal: str):
        if not path or not principal.strip():
            raise SourceError("archive_not_configured", "Set JT_EVIDENCE_DB and JT_PRINCIPAL")
        self.path, self.principal = path, principal
        with private_database(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS snapshots "
                "(id TEXT PRIMARY KEY, principal TEXT, kind TEXT, body TEXT, hash TEXT)"
            )

    def put(self, kind, value, identifier=None):
        identifier = identifier or "record_" + uuid.uuid4().hex
        body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with private_database(self.path) as db:
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?)",
                (identifier, self.principal, kind, body, digest(body)),
            )
        return identifier

    def get(self, kind, identifier):
        with private_database(self.path) as db:
            row = db.execute(
                "SELECT body,hash FROM snapshots WHERE id=? AND principal=? AND kind=?",
                (identifier, self.principal, kind),
            ).fetchone()
        if row is None:
            raise SourceError("evidence_unavailable", "Snapshot unavailable for this principal")
        if digest(row[0]) != row[1]:
            raise SourceError("archive_corrupted", "Snapshot integrity check failed")
        return json.loads(row[0])
