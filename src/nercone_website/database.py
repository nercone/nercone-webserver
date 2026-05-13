import sqlite3
from .config import Files

class AccessCounter:
    def _connect(self):
        conn = sqlite3.connect(Files.Databases.access_counter)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def __init__(self):
        conn = self._connect()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS access_counter (
            value INTEGER NOT NULL
        )
        """)
        conn.execute("INSERT OR IGNORE INTO access_counter (rowid, value) VALUES (1, 0)")
        conn.commit()
        conn.close()

    def get(self) -> int:
        conn = self._connect()
        cur = conn.execute("SELECT value FROM access_counter WHERE rowid = 1")
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def increase(self):
        conn = self._connect()
        conn.execute("UPDATE access_counter SET value = value + 1 WHERE rowid = 1")
        conn.commit()
        conn.close()
