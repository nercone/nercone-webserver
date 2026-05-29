import httpx
import fcntl
import mimetypes
from datetime import datetime, timedelta

from .logger import Logger
from .constants import Files

class MimeTypes:
    url = "https://raw.githubusercontent.com/apache/httpd/trunk/docs/conf/mime.types"
    max_age = timedelta(days=30)

    @staticmethod
    def fetch():
        if Files.mime_types.exists():
            age = datetime.now() - datetime.fromtimestamp(Files.mime_types.stat().st_mtime)
            if age < MimeTypes.max_age:
                return
        try:
            with httpx.Client(http2=True, timeout=30) as client:
                response = client.get(MimeTypes.url)
                response.raise_for_status()
            Files.mime_types.write_text(response.text, encoding="utf-8")
        except Exception as e:
            Logger.log(f"MimeTypes: Failed to fetch mime.types: {e}")

    @staticmethod
    def load():
        if not Files.mime_types.exists():
            return
        extra = mimetypes.read_mime_types(str(Files.mime_types))
        if extra:
            for ext, mime in extra.items():
                mimetypes.add_type(mime, ext)

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
