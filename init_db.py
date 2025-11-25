import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"
SQL_FILE = Path(__file__).parent / "schema.sql"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Initialized DB at {DB_PATH}")

if __name__ == "__main__":
    init_db()
