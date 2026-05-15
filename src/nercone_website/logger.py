import time
from datetime import datetime, timezone
from starlette.types import Scope
from .database import insert_access_log

def log_access(id: str, scope: Scope) -> dict:
    client = scope.get("client") or ("", 0)
    server = scope.get("server") or ("", 0)
    headers = dict(scope.get("headers", []))
    hostname = headers.get(b"host", b"").decode().split(":")[0].strip()
    return {
        "id": id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": {
            "address": client[0],
            "port": client[1],
            "trusted": scope.get("trusted", False)
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

async def finalize_log(log: dict, status_code: int, start_time: float, timings: dict | None = None) -> dict:
    log["status_code"] = status_code
    log["duration"] = round((time.perf_counter() - start_time) * 1000, 3)
    if timings:
        log["timings"] = {k: round(v, 3) for k, v in timings.items()}
    await insert_access_log(log)
    return log
