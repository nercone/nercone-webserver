import fcntl
from .constants import Files

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
