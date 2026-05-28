import fcntl
from pathlib import Path
from .constants import Files

class Logger:
    @staticmethod
    def log(*contents: str, path: Path = Files.Logs.access):
        with path.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(" ".join(contents))
