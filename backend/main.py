from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3

app = FastAPI()
DB_PATH = "brain.db"

class Message(BaseModel):
    platform: str
    timestamp: str
    sender: str
    recipient: Optional[str] = None
    group_participants: Optional[str] = None
    text: str

def row_to_dict(row):
    return {
        "id": row[0],
        "platform": row[1],
        "timestamp": row[2],
        "sender": row[3],
        "recipient": row[4],
        "group_participants": row[5],
        "text": row[6],
        "is_embedded": row[7],
    }

@app.post("/messages/")
def create_message(msg: Message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO growing_messages 
        (platform, timestamp, sender, recipient, group_participants, text) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (msg.platform, msg.timestamp, msg.sender, msg.recipient, msg.group_participants, msg.text))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return {"message": "Inserted", "id": msg_id}

@app.get("/messages/", response_model=List[dict])
def get_all_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM growing_messages")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

@app.get("/messages/{message_id}")
def get_message_by_id(message_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM growing_messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    return row_to_dict(row)

@app.get("/messages/contact/{contact}")
def get_messages_by_contact(contact: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM growing_messages 
        WHERE sender = ? OR recipient = ? OR group_participants LIKE ?
    """, (contact, contact, f"%{contact}%"))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]
