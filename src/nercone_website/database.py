import sqlite3
from .config import Files

class AccessCounter:
    def __init__(self):
        self._conn = sqlite3.connect(Files.Databases.access_counter)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS access_counter (
            value INTEGER NOT NULL
        )
        """)
        self._conn.execute("INSERT OR IGNORE INTO access_counter (rowid, value) VALUES (1, 0)")
        self._conn.commit()

    def get(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM access_counter WHERE rowid = 1")
        row = cur.fetchone()
        return row[0] if row else 0

    def increase(self):
        self._conn.execute("UPDATE access_counter SET value = value + 1 WHERE rowid = 1")
        self._conn.commit()
