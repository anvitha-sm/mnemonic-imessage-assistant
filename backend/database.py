import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "brain.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS growing_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        timestamp TEXT,
        sender TEXT,
        recipient TEXT,
        group_participants TEXT,
        text TEXT,
        is_embedded INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()
