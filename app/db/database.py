"""Opening connections to the SQLite database created by data/seed.py."""

import sqlite3
from pathlib import Path

# app/db/database.py -> parents[2] is the project root.
DB_PATH = Path(__file__).parents[2] / "data" / "shop.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    # Rows behave like dicts: row["price_gbp"] instead of row[4].
    conn.row_factory = sqlite3.Row
    return conn
