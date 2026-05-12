import sqlite3
from .config import Files

class AccessCounter:
    def __init__(self):
        if not Files.Databases.access_counter.is_file():
            conn = sqlite3.connect(Files.Databases.access_counter)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS access_counter (
                value INTEGER NOT NULL
            )
            """)
            conn.execute("INSERT OR IGNORE INTO access_counter (rowid, value) VALUES (1, 0)")
            conn.commit()
            conn.close()

    def get(self) -> int:
        conn = sqlite3.connect(Files.Databases.access_counter)
        try:
            cur = conn.cursor()
            cur.execute("SELECT value FROM access_counter WHERE rowid = 1")
            row = cur.fetchone()
            if row is None:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS access_counter (
                    value INTEGER NOT NULL
                )
                """)
                conn.execute("INSERT OR IGNORE INTO access_counter (rowid, value) VALUES (1, 0)")
                conn.commit()
                return 0
            return row[0]
        finally:
            conn.close()

    def increase(self):
        conn = sqlite3.connect(Files.Databases.access_counter)
        try:
            cur = conn.cursor()
            conn.execute("BEGIN IMMEDIATE")
            cur.execute(
                "UPDATE access_counter SET value = value + 1 WHERE rowid = 1"
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
