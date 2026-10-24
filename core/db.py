"""Database layer.

Runs on a local SQLite file by default. If TURSO_DATABASE_URL is set (secrets or
environment), the same SQL runs against a hosted Turso database instead, which
is what keeps data safe on Streamlit Community Cloud. Prices are integer paise.
"""
import sqlite3
from contextlib import contextmanager

import streamlit as st

from .config import DB_PATH, get_secret

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )""",
    # Images live in the database (base64 text) so they survive redeploys.
    """CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mime TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )""",
    """CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE
    )""",
    """CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER NOT NULL REFERENCES users(id),
        category_id INTEGER REFERENCES categories(id),
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        condition TEXT NOT NULL DEFAULT 'Used',
        image_id INTEGER REFERENCES images(id),
        starting_price INTEGER NOT NULL CHECK (starting_price > 0),
        min_increment INTEGER NOT NULL CHECK (min_increment > 0),
        current_price INTEGER NOT NULL,
        reserve_price INTEGER,
        bid_count INTEGER NOT NULL DEFAULT 0,
        leader_id INTEGER REFERENCES users(id),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK (status IN ('active', 'ended', 'cancelled', 'removed')),
        winner_id INTEGER REFERENCES users(id),
        winning_amount INTEGER,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )""",
    """CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id INTEGER NOT NULL REFERENCES auctions(id),
        bidder_id INTEGER NOT NULL REFERENCES users(id),
        amount INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )""",
    """CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id INTEGER NOT NULL UNIQUE REFERENCES auctions(id),
        buyer_id INTEGER NOT NULL REFERENCES users(id),
        amount INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending', 'submitted', 'confirmed')),
        reference TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        confirmed_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_auctions_status_end ON auctions(status, end_time)",
    "CREATE INDEX IF NOT EXISTS idx_auctions_seller ON auctions(seller_id)",
    "CREATE INDEX IF NOT EXISTS idx_bids_auction_amount ON bids(auction_id, amount)",
    "CREATE INDEX IF NOT EXISTS idx_bids_bidder ON bids(bidder_id)",
]

DEFAULT_CATEGORIES = [
    "Electronics",
    "Collectibles",
    "Art and Decor",
    "Fashion and Jewellery",
    "Home and Garden",
    "Vehicles",
    "Books and Media",
    "Sports and Outdoors",
]

DEFAULT_SETTINGS = {
    "min_increment_floor": "1000",  # paise, i.e. 10 rupees
    "payment_payee_name": "",
    "payment_instructions": "Scan the QR code with any UPI app, pay the exact amount "
    "shown, then enter your transaction reference and confirm.",
    "payment_qr_image_id": "",
}


def using_hosted_db() -> bool:
    return bool(get_secret("TURSO_DATABASE_URL"))


def _connect():
    url = get_secret("TURSO_DATABASE_URL")
    if url:
        import libsql  # imported lazily so local runs do not need it

        return libsql.connect(database=url, auth_token=get_secret("TURSO_AUTH_TOKEN"))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def connection():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def rows(cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(cols, r)) for r in cursor.fetchall()]


def fetch_all(sql: str, params=()) -> list[dict]:
    with connection() as conn:
        return rows(conn.execute(sql, tuple(params)))


def fetch_one(sql: str, params=()):
    result = fetch_all(sql, params)
    return result[0] if result else None


def execute(sql: str, params=()) -> None:
    with connection() as conn:
        conn.execute(sql, tuple(params))


def insert(sql: str, params=()) -> int:
    """Run an INSERT and return the new row id."""
    with connection() as conn:
        result = rows(conn.execute(sql.rstrip().rstrip(";") + " RETURNING id", tuple(params)))
    return int(result[0]["id"])


def get_setting(key: str, default: str = "") -> str:
    row = fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else DEFAULT_SETTINGS.get(key, default)


def set_setting(key: str, value: str) -> None:
    execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


@st.cache_resource(show_spinner=False)
def init_db() -> bool:
    """Create tables and seed defaults. Runs once per server process."""
    with connection() as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        for name in DEFAULT_CATEGORIES:
            conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    return True
