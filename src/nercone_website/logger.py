import json
import fcntl
import logging
from pathlib import Path
from fastapi import Request, Response

from .constants import Files

logger = logging.getLogger("website")

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
        Logger.log(json.dumps(log) + "\n", path=Files.Logs.access)
        logger.info(f"[{request.scope['id'].text}] STATUS {response.status_code} FROM {request.client.host}:{request.client.port} TO {str(request.url)}")

    @staticmethod
    def log_error(id: str, traceback: str):
        Logger.log(f"[{id}]\n{traceback}\n", path=Files.Logs.error)
        logger.error(f"[{id}] STATUS 500")
