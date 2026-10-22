"""SQLite: persiste apenas metadados, texto e estado; nunca tokens da Meta."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def initialize(self) -> None:
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    contact TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('inbound', 'outbound')),
                    kind TEXT NOT NULL,
                    body TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_contact_time
                    ON messages(contact, timestamp DESC);
                CREATE TABLE IF NOT EXISTS prepared (
                    token_hash TEXT PRIMARY KEY,
                    contact TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT 'ready',
                    message_id TEXT
                );
            """)
        if os.name == "posix":
            os.chmod(self.path, 0o600)

    def inbound(self, message_id: str, contact: str, kind: str, body: str, timestamp: int) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "INSERT OR IGNORE INTO messages VALUES (?, ?, 'inbound', ?, ?, ?, 'received')",
                (message_id, contact, kind, body, timestamp),
            )
            return cur.rowcount == 1

    def outbound(self, message_id: str, contact: str, kind: str, body: str) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO messages VALUES (?, ?, 'outbound', ?, ?, ?, 'accepted')",
                (message_id, contact, kind, body, int(time.time())),
            )

    def update_status(self, message_id: str, status: str) -> None:
        if status not in {"sent", "delivered", "read", "failed"}:
            return
        with self.connect() as db:
            db.execute("UPDATE messages SET status=? WHERE id=? AND direction='outbound'",
                       (status, message_id))

    def conversations(self, limit: int) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("""
                SELECT contact, COUNT(*) AS message_count, MAX(timestamp) AS last_message_at
                  FROM messages GROUP BY contact ORDER BY last_message_at DESC LIMIT ?
            """, (max(1, min(limit, 50)),)).fetchall()
        return [dict(row) for row in rows]

    def messages(self, contact: str, limit: int) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("""
                SELECT id, contact, direction, kind, body, timestamp, status
                  FROM messages WHERE contact=?
                  ORDER BY timestamp DESC, rowid DESC LIMIT ?
            """, (contact, max(1, min(limit, 50)))).fetchall()
        return [dict(row) for row in rows]

    def search(self, text: str, contact: str, limit: int) -> list[dict[str, Any]]:
        if not text.strip() or len(text) > 200:
            raise ValueError("Consulta obrigatória (máximo 200 caracteres)")
        with self.connect() as db:
            rows = db.execute("""
                SELECT id, contact, direction, kind, body, timestamp, status
                  FROM messages
                 WHERE instr(lower(body), lower(?)) > 0
                   AND (? = '' OR contact = ?)
                 ORDER BY timestamp DESC, rowid DESC LIMIT ?
            """, (text, contact, contact, max(1, min(limit, 50)))).fetchall()
        return [dict(row) for row in rows]

    def last_inbound(self, contact: str) -> int | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT MAX(timestamp) AS ts FROM messages WHERE contact=? AND direction='inbound'",
                (contact,),
            ).fetchone()
        return row["ts"]

    def prepare(self, contact: str, payload: dict[str, Any], ttl: int) -> str:
        approval_token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(approval_token.encode()).hexdigest()
        now = int(time.time())
        with self.connect() as db:
            db.execute("DELETE FROM prepared WHERE expires_at < ? AND state='ready'", (now,))
            db.execute(
                "INSERT INTO prepared (token_hash, contact, payload, expires_at) VALUES (?, ?, ?, ?)",
                (digest, contact, json.dumps(payload, ensure_ascii=False), now + ttl),
            )
        return approval_token

    def reserve(self, approval_token: str) -> tuple[str, dict[str, Any]]:
        digest = hashlib.sha256(approval_token.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT contact, payload FROM prepared WHERE token_hash=?"
                             " AND state='ready' AND expires_at>=?",
                             (digest, int(time.time()))).fetchone()
            if row is None:
                raise ValueError("Preparação expirada, desconhecida ou já utilizada")
            db.execute("UPDATE prepared SET state='sending' WHERE token_hash=?", (digest,))
        return row["contact"], json.loads(row["payload"])

    def finalize(self, approval_token: str, status: str, message_id: str = "") -> None:
        digest = hashlib.sha256(approval_token.encode()).hexdigest()
        with self.connect() as db:
            db.execute("UPDATE prepared SET state=?, message_id=? WHERE token_hash=?"
                       " AND state='sending'", (status, message_id, digest))
