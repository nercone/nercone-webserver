import time
import uuid
import json
from starlette.types import Scope
from datetime import datetime, timezone
from .config import Files, AccessSources

def log_access(scope: Scope, id: str = None, write: bool = False) -> tuple[dict, float]:
    client = scope.get("client") or ("", 0)
    server = scope.get("server") or ("", 0)
    headers = dict(scope.get("headers", []))
    hostname = headers.get(b"host", b"").decode().split(":")[0].strip()
    log = {
        "id": id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": {
            "address": client[0],
            "port": client[1],
            "trusted": AccessSources.is_trusted(scope.get("client", ("", 0))[0], headers.get(b"x-forwarded-for", b"").decode())
        },
        "to": {
            "scheme": scope.get("scheme", "https"),
            "host": hostname,
            "port": server[1]
        },
        "method": scope.get("method", "GET"),
        "path": scope.get("path", "/"),
        "headers": {k.decode(): v.decode() for k, v in headers.items()}
    }
    if write:
        write_log(log)
    return log

def finalize_log(log: dict, status_code: int, start_time: float, timings: dict | None = None, write: bool = True) -> dict:
    log["status_code"] = status_code
    log["duration"] = round((time.perf_counter() - start_time) * 1000, 3)
    if timings:
        log["timings"] = {k: round(v, 3) for k, v in timings.items()}
    if write:
        write_log(log)
    return log

def write_log(log: dict) -> None:
    with Files.Logs.access.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")
