from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "compiler.db")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              source_hash TEXT NOT NULL,
              source_text TEXT NOT NULL,
              ok INTEGER NOT NULL,
              output_text TEXT NOT NULL,
              error_text TEXT NOT NULL,
              bytecode_json TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_run(
    *,
    source_hash: str,
    source_text: str,
    ok: bool,
    output_text: str,
    error_text: str,
    bytecode: Any,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO runs (created_at, source_hash, source_text, ok, output_text, error_text, bytecode_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _utc_now_iso(),
                source_hash,
                source_text,
                1 if ok else 0,
                output_text,
                error_text,
                json.dumps(bytecode),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()

