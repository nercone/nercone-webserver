import json
import fcntl
import logging
from pathlib import Path
from fastapi import Request, Response

from .constants import Files

class Logger:
    @staticmethod
    def log(*contents: str, end: str = "\n", path: Path = Files.Logs.app):
        with path.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(" ".join(contents) + end)

    @staticmethod
    def log_access(request: Request, response: Response):
        log = {
            "id": request.scope["id"].text,
            "url": str(request.url),
            "status": response.status_code,
            "method": request.method,
            "client": {
                "host": request.client.host,
                "port": request.client.port
            },
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
        Logger.log(json.dumps(log), path=Files.Logs.access)
        Logger.log(f"[{request.scope['id'].compact_text}] STATUS {response.status_code} FROM {request.client.host}:{request.client.port} TO {str(request.url)}")

    @staticmethod
    def log_error(id: str, traceback: str):
        Logger.log(f"[{id}]\n{traceback}", path=Files.Logs.error)
        Logger.log(f"[{id}] STATUS 500")
