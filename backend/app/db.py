import sqlite3
from pathlib import Path
from .config import DATABASE_PATH

def connect():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL, document_type TEXT NOT NULL, document_date TEXT,
      language TEXT DEFAULT 'Unknown', original_filename TEXT,
      extracted_text TEXT DEFAULT '', summary TEXT DEFAULT '',
      status TEXT DEFAULT 'Needs review', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn

def serialize(row):
    return {"id": row["id"], "name": row["name"], "type": row["document_type"],
      "date": row["document_date"] or "", "language": row["language"] or "Unknown",
      "filename": row["original_filename"] or "", "text": row["extracted_text"] or "",
      "summary": row["summary"] or "", "status": row["status"] or "Needs review",
      "createdAt": row["created_at"]}
