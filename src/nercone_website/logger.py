import json
import fcntl
from pathlib import Path
from fastapi import Request, Response

from .constants import Files

class Logger:
    @staticmethod
    def log(*contents: str, path: Path = Files.Logs.app):
        with path.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(" ".join(contents))

    @staticmethod
    def log_access(request: Request, response: Response):
        log = {
            "id": request.scope["id"].text,
            "url": str(request.url),
            "status": response.status_code,
            "method": request.method,
            "headers": {
                "request": dict(request.headers),
                "response": dict(response.headers)
            },
            "managers": {
                "pp": request.scope["pp"].directives,
                "csp": request.scope["csp"].directives,
                "timings": request.scope["timings"].timings,
                "network": {"trusted": request.scope["network"].trusted}
            }
        }
        Logger.log(json.dumps(log) + "\n", path=Files.Logs.access)

    @staticmethod
    def log_error(id: str, traceback: str):
        Logger.log(f"[{id}]\n{traceback}\n", path=Files.Logs.error)
