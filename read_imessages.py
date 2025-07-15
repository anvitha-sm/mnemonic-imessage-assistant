import sqlite3
import json
from datetime import datetime
from get_contacts import get_contacts, get_group_participants

chat_connect = sqlite3.connect("/Users/annie1/Library/Messages/chat.db")
chat_cursor = chat_connect.cursor()

brain_connect = sqlite3.connect("brain.db")
brain_cursor = brain_connect.cursor()

contact_map = get_contacts()

brain_cursor.execute("SELECT MAX(timestamp) FROM messages WHERE platform = 'iMessage';")
last_timestamp_row = brain_cursor.fetchone()
last_timestamp = last_timestamp_row[0] if last_timestamp_row[0] else "2025-07-14 00:00:00"
unix_cutoff = int(datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S").timestamp())

chat_cursor.execute("""
  SELECT ROWID FROM message
  WHERE date > (? - strftime('%s', '2001-01-01')) * 1000000000
  ORDER BY date ASC;
""", (unix_cutoff,))

new_ids = [row[0] for row in chat_cursor.fetchall()]
if new_ids:
    placeholders = ','.join(['?'] * len(new_ids))
    query = f"""
    SELECT
      datetime(m.date / 1000000000 + strftime('%s', '2001-01-01'), 'unixepoch', 'localtime') AS message_date,
      h.id AS sender_handle,
      m.is_from_me,
      m.text,
      cmj.chat_id,
      c.display_name AS display_name,
      cmj.chat_id AS other_recip
    FROM message m
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    LEFT JOIN chat c ON cmj.chat_id = c.ROWID
    WHERE m.ROWID IN ({placeholders})
    ORDER BY m.date ASC;
    """

    chat_cursor.execute(query, new_ids)
    for row in chat_cursor.fetchall():
        message_date, sender_handle, is_from_me, text, chat_id, display_name, other_recip = row

        platform = "iMessage"
        if is_from_me:
            sender = "Me"
        else:
            sender = contact_map.get(sender_handle, sender_handle) if sender_handle else "Unknown"

        if display_name: 
            recipient = display_name
            group_participants = json.dumps(get_group_participants(chat_cursor, other_recip, contact_map))
        elif is_from_me:  
            group_participants = get_group_participants(chat_cursor, other_recip, contact_map)[0]
            recipient = group_participants
        else:  
            recipient = "Me"
            group_participants = sender

        if text:
            brain_cursor.execute("""
              INSERT INTO growing_messages (platform, timestamp, sender, recipient, group_participants, text, is_embedded)
              VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (platform, message_date, sender, recipient, group_participants, text))
    brain_connect.commit()

chat_connect.close()
brain_connect.close()
