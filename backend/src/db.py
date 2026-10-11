"""SQLite storage for PantryPal.

This module opens the database, creates tables, and seeds a demo household.
Business rules live in inventory.py. HTTP lives in app.py.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path


DEFAULT_PATH = str(Path(__file__).resolve().parent.parent / "data" / "household.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('fridge', 'freezer', 'pantry', 'other')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    shelf_life_days INTEGER NOT NULL CHECK (shelf_life_days >= 0),
    par_quantity REAL NOT NULL CHECK (par_quantity >= 0),
    preferred_location_id INTEGER REFERENCES locations(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    location_id INTEGER NOT NULL REFERENCES locations(id),
    quantity_added REAL NOT NULL CHECK (quantity_added > 0),
    quantity_remaining REAL NOT NULL CHECK (quantity_remaining >= 0),
    added_on TEXT NOT NULL,
    expires_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'depleted', 'wasted'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    lot_id INTEGER REFERENCES lots(id),
    location_id INTEGER REFERENCES locations(id),
    event_type TEXT NOT NULL CHECK (event_type IN ('stocked', 'consumed', 'wasted', 'moved')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    occurred_on TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_lots_status_location ON lots(status, location_id);
CREATE INDEX IF NOT EXISTS idx_events_product_type ON events(product_id, event_type, occurred_on);
"""


def connect(path):
    """Open SQLite with foreign keys and row access by column name.

    Args:
        path: File path, or ":memory:" for a private database.

    Returns:
        An open sqlite3.Connection. The caller commits and closes it.
    """
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn, seed=True, today=None):
    """Create tables and, when products is empty, load the demo household.

    Args:
        conn: Open connection from connect().
        seed: When True, fill an empty database with demo data.
        today: Date the demo history is built around. Defaults to the real today.

    The demo import is lazy so this module can be imported without the
    service layer, and so seeding goes through the same functions as the API.
    """
    conn.executescript(SCHEMA)
    if seed and _is_empty(conn, "products"):
        from inventory import seed_demo

        seed_demo(conn, today or date.today())
    conn.commit()


def _is_empty(conn, table):
    row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
    return row["n"] == 0


@contextmanager
def session(path):
    """Commit on success and roll back on any error.

    Args:
        path: Database file passed to connect().

    Yields:
        An open connection.
    """
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
