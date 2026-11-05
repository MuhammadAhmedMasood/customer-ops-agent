"""Create data/shop.db with ~20 sample orders and empty `tickets` and `replies` tables.

Run from the project root:
    python data/seed.py

Safe to run again: it drops and recreates the table each time.
"""

import sqlite3
from pathlib import Path

# Put shop.db next to this script, wherever you run it from.
DB_PATH = Path(__file__).parent / "shop.db"

# delivery_date is the actual delivery date, or None if not delivered yet.
# Columns: order_id, customer_name, email, item, price_gbp, status, order_date, delivery_date
ORDERS = [
    ("SC-1001", "Amelia Hughes", "amelia.hughes@example.com", "Wireless headphones", 89.99, "delivered", "2026-10-02", "2026-10-05"),
    ("SC-1002", "Oliver Patel", "oliver.patel@example.com", "Phone case", 14.50, "delivered", "2026-10-04", "2026-10-07"),
    ("SC-1003", "Isla Thompson", "isla.thompson@example.com", "Running shoes", 74.00, "shipped", "2026-11-01", None),
    ("SC-1004", "Harry Khan", "harry.khan@example.com", "USB-C charger", 19.99, "processing", "2026-11-04", None),
    ("SC-1005", "Sophia Evans", "sophia.evans@example.com", "Coffee machine", 149.00, "delayed", "2026-10-20", None),
    ("SC-1006", "Jack Wilson", "jack.wilson@example.com", "Desk lamp", 32.00, "returned", "2026-09-28", "2026-10-01"),
    ("SC-1007", "Mia Roberts", "mia.roberts@example.com", "Winter coat", 120.00, "delivered", "2026-10-15", "2026-10-18"),
    ("SC-1008", "Noah Ahmed", "noah.ahmed@example.com", "Board game", 27.99, "shipped", "2026-11-02", None),
    ("SC-1009", "Grace Walker", "grace.walker@example.com", "Smart watch", 199.99, "delayed", "2026-10-25", None),
    ("SC-1010", "Leo Clarke", "leo.clarke@example.com", "Water bottle", 12.00, "delivered", "2026-10-10", "2026-10-12"),
    ("SC-1011", "Ava Wright", "ava.wright@example.com", "Bluetooth speaker", 55.00, "delivered", "2026-10-22", "2026-10-25"),
    ("SC-1012", "George Hall", "george.hall@example.com", "Yoga mat", 25.00, "processing", "2026-11-05", None),
    ("SC-1013", "Freya Green", "freya.green@example.com", "Air fryer", 79.99, "returned", "2026-10-01", "2026-10-04"),
    ("SC-1014", "Muhammad Ali", "muhammad.ali@example.com", "Gaming mouse", 45.00, "delivered", "2026-10-28", "2026-10-31"),
    ("SC-1015", "Lily Baker", "lily.baker@example.com", "Bed sheets set", 39.99, "delayed", "2026-10-24", None),
    ("SC-1016", "Thomas Scott", "thomas.scott@example.com", "Office chair", 179.00, "shipped", "2026-10-30", None),
    ("SC-1017", "Emily Turner", "emily.turner@example.com", "Notebook pack", 8.99, "delivered", "2026-10-18", "2026-10-21"),
    ("SC-1018", "Arthur Lewis", "arthur.lewis@example.com", "Electric toothbrush", 64.99, "delivered", "2026-10-26", "2026-10-29"),
    ("SC-1019", "Ella Young", "ella.young@example.com", "Backpack", 49.99, "processing", "2026-11-03", None),
    ("SC-1020", "Henry Morris", "henry.morris@example.com", "Tablet", 299.00, "delivered", "2026-10-08", "2026-10-11"),
]


def seed(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute(
        """
        CREATE TABLE orders (
            order_id      TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email         TEXT NOT NULL,
            item          TEXT NOT NULL,
            price_gbp     REAL NOT NULL,
            status        TEXT NOT NULL CHECK (status IN
                            ('processing', 'shipped', 'delivered', 'delayed', 'returned')),
            order_date    TEXT NOT NULL,
            delivery_date TEXT
        )
        """
    )
    # The ? placeholders let sqlite3 insert values safely (no string-building SQL).
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ORDERS)

    # Tickets received by the webhook. Starts empty on every seed.
    cur.execute("DROP TABLE IF EXISTS tickets")
    cur.execute(
        """
        CREATE TABLE tickets (
            ticket_id      TEXT PRIMARY KEY,
            customer_email TEXT NOT NULL,
            subject        TEXT NOT NULL,
            message        TEXT NOT NULL,
            order_id       TEXT,
            status         TEXT NOT NULL DEFAULT 'received',
            category       TEXT,
            result         TEXT,  -- JSON summary of the agent run, for the demo page
            created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Replies written back to the mock helpdesk. Starts empty on every seed.
    cur.execute("DROP TABLE IF EXISTS replies")
    cur.execute(
        """
        CREATE TABLE replies (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id      TEXT NOT NULL,
            reply_text     TEXT NOT NULL,
            action         TEXT NOT NULL,
            needs_approval INTEGER NOT NULL,
            status         TEXT NOT NULL CHECK (status IN ('sent', 'pending_approval', 'approved')),
            created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"Seeded {len(ORDERS)} orders into {db_path}")


if __name__ == "__main__":
    seed()
