from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from database import get_connection, init_db
from datetime import datetime

app = FastAPI()
init_db()

class Message(BaseModel):
    platform: str
    timestamp: str
    sender: str
    recipient: Optional[str] = None
    group_participants: Optional[str] = None
    text: str
    is_embedded: int = 0

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

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False

@app.post("/api/messages/")
def add_message(message: Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO growing_messages (platform, timestamp, sender, recipient, group_participants, text, is_embedded)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        message.platform, message.timestamp, message.sender,
        message.recipient, message.group_participants,
        message.text, message.is_embedded
    ))
    conn.commit()
    conn.close()
    return {"status": "Message stored"}

@app.get("/api/messages/")
def get_all_messages(
    since: Optional[str] = Query(None, description="Filter messages after this timestamp (YYYY-MM-DD HH:MM:SS)")
):
    if since and not validate_date(since):
        raise HTTPException(status_code=400, detail="Invalid date format for 'since'. Use YYYY-MM-DD HH:MM:SS")

    conn = get_connection()
    cursor = conn.cursor()
    if since:
        cursor.execute("""
            SELECT * FROM growing_messages
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """, (since,))
    else:
        cursor.execute("SELECT * FROM growing_messages ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

@app.get("/api/messages/{message_id}")
def get_message_by_id(message_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM growing_messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row_to_dict(row)
    raise HTTPException(status_code=404, detail="Message not found")

@app.get("/api/messages/by_contact/{contact}")
def get_messages_by_contact(contact: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM growing_messages 
        WHERE sender = ? OR recipient = ? OR group_participants LIKE ?
        ORDER BY timestamp ASC
    """, (contact, contact, f"%{contact}%"))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

@app.get("/api/messages/by_group/{group_name}")
def get_messages_by_group(group_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM growing_messages
        WHERE LOWER(group_participants) LIKE LOWER(?)
        ORDER BY timestamp ASC
    """, (f"%{group_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

@app.get("/api/messages/by_time/")
def get_messages_by_time(
    start: str = Query(..., description="Start timestamp (YYYY-MM-DD HH:MM:SS)"),
    end: str = Query(..., description="End timestamp (YYYY-MM-DD HH:MM:SS)")
):
    if not (validate_date(start) and validate_date(end)):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD HH:MM:SS")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM growing_messages
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start, end))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

@app.get("/api/messages/by_filter/")
def get_messages_by_filter(
    start: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD HH:MM:SS)"),
    end: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD HH:MM:SS)"),
    contact: Optional[str] = Query(None, description="Contact name to filter"),
    group: Optional[str] = Query(None, description="Group name to filter"),
):
    if start and not validate_date(start):
        raise HTTPException(status_code=400, detail="Invalid date format for 'start'. Use YYYY-MM-DD HH:MM:SS")
    if end and not validate_date(end):
        raise HTTPException(status_code=400, detail="Invalid date format for 'end'. Use YYYY-MM-DD HH:MM:SS")

    query = "SELECT * FROM growing_messages"
    conditions = []
    params = []

    if start and end:
        conditions.append("timestamp BETWEEN ? AND ?")
        params.extend([start, end])
    elif start:
        conditions.append("timestamp >= ?")
        params.append(start)
    elif end:
        conditions.append("timestamp <= ?")
        params.append(end)

    if contact:
        conditions.append("(sender = ? OR recipient = ? OR group_participants LIKE ?)")
        params.extend([contact, contact, f"%{contact}%"])
    if group:
        conditions.append("LOWER(group_participants) LIKE LOWER(?)")
        params.append(f"%{group}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp ASC"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

