"""SQLite persistence layer for the Streamlit MVP."""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
DEFAULT_DB_PATH = os.getenv("PDI_DB_PATH", "data/pdi.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def session(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 provider TEXT NOT NULL,
 external_id TEXT NOT NULL,
 title TEXT NOT NULL,
 brand TEXT, model TEXT, gtin TEXT, sku TEXT,
 image_url TEXT, source_url TEXT,
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 updated_at TEXT NOT NULL DEFAULT (datetime('now')),
 UNIQUE(provider, external_id)
);
CREATE TABLE IF NOT EXISTS price_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL,
 provider TEXT NOT NULL,
 store TEXT NOT NULL,
 price REAL NOT NULL,
 shipping REAL,
 effective_price REAL NOT NULL,
 captured_at TEXT NOT NULL DEFAULT (datetime('now')),
 FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE INDEX IF NOT EXISTS idx_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_history_captured ON price_history(captured_at);
CREATE TABLE IF NOT EXISTS searches (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 raw_query TEXT NOT NULL,
 normalized_json TEXT,
 result_count INTEGER NOT NULL DEFAULT 0,
 provider TEXT,
 captured_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS watchlist (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 query TEXT NOT NULL UNIQUE,
 target_price REAL,
 maximum_price REAL,
 alert_enabled INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

def init_db(db_path: Optional[str] = None) -> None:
    with session(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
