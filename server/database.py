import sqlite3
import json
from pathlib import Path
from datetime import datetime

base_dir = Path(__file__).resolve().parent
DB_PATH = base_dir / "tasks.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS intake_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                intent TEXT,
                entities TEXT,
                confidence REAL,
                route TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        """)
        conn.commit()

def insert_task(raw_message: str, intent: str, entities: dict, confidence: float, route: str, notes: str = "") -> int:
    """Takes in user message and chatbot parse adding to database table"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO intake_tasks (created_at, raw_message, intent, entities, confidence, route, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                datetime.utcnow().isoformat(),
                raw_message,
                intent,
                json.dumps(entities),
                confidence,
                route,
                notes,
            ),
        )
        conn.commit()
        return cursor.lastrowid

 
def get_all_tasks():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM intake_tasks ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]
 
 
def update_task_status(task_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE intake_tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        conn.commit()