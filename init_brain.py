import sqlite3

brain_connect = sqlite3.connect("brain.db")
brain_cursor = brain_connect.cursor()
query = """
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
"""
brain_cursor.execute(query)
brain_connect.commit()
brain_connect.close()