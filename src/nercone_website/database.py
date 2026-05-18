import json
import fcntl
import asyncpg
from datetime import datetime
from .config import Files, Options

pool: asyncpg.Pool | None = None

async def setup_connection(conn: asyncpg.Connection):
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(Options.database_url, setup=setup_connection)
    async with pool.acquire() as conn:
        await conn.execute("""
            DO $$
            BEGIN
                IF (SELECT data_type FROM information_schema.columns
                    WHERE table_name='access_logs' AND column_name='id') = 'uuid' THEN
                    ALTER TABLE access_logs ALTER COLUMN id TYPE TEXT USING id::text;
                END IF;
            END $$;
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id            TEXT        PRIMARY KEY,
                timestamp     TIMESTAMPTZ NOT NULL,
                from_address  TEXT,
                from_port     INTEGER,
                from_trusted  BOOLEAN,
                to_scheme     TEXT,
                to_host       TEXT,
                to_port       INTEGER,
                method        TEXT,
                path          TEXT,
                req_headers   JSONB,
                status_code   INTEGER,
                duration_ms   FLOAT,
                timings       JSONB
            )
        """)

async def insert_access_log(log: dict):
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO access_logs
                   (id, timestamp, from_address, from_port, from_trusted,
                    to_scheme, to_host, to_port, method, path,
                    req_headers, status_code, duration_ms, timings)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
                log["id"],
                datetime.fromisoformat(log["timestamp"]),
                log["from"]["address"],
                log["from"]["port"],
                log["from"]["trusted"],
                log["to"]["scheme"],
                log["to"]["host"],
                log["to"]["port"],
                log["method"],
                log["path"],
                log.get("headers"),
                log.get("status_code"),
                log.get("duration"),
                log.get("timings"),
            )
    except Exception:
        pass

class AccessCounter:
    def __init__(self):
        if not Files.access_counter.exists():
            Files.access_counter.write_text("0", encoding="utf-8")

    def get(self) -> int:
        try:
            return int(Files.access_counter.read_text(encoding="utf-8").strip())
        except (ValueError, FileNotFoundError):
            return 0

    def increase(self):
        with Files.access_counter.open("r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                value = int(f.read().strip())
            except ValueError:
                value = 0
            f.seek(0)
            f.write(str(value + 1))
            f.truncate()
