import os
import libsql

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def get_connection():
    """Connects to Turso cloud database using HTTP tokens or local fallback."""
    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
        # Pass explicit timeouts or HTTP mode to avoid hanging connections
        return libsql.connect(database=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
    else:
        return libsql.connect("inventory.db")

def init_db():
    conn = None
    try:
        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                expiry_date TEXT,
                notified INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    finally:
        if conn:
            conn.close()

def add_item_to_db(name, expiry_date_str):
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO items (name, expiry_date, notified) VALUES (?, ?, 0)",
            (name, expiry_date_str)
        )
        conn.commit()
    finally:
        if conn:
            conn.close()

def delete_item_from_db(item_id):
    conn = None
    try:
        conn = get_connection()
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        if conn:
            conn.close()

def get_items_from_db():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, expiry_date FROM items ORDER BY expiry_date ASC")
        rows = cursor.fetchall()
        return rows
    finally:
        if conn:
            conn.close()