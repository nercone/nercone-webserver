import time
import fcntl
import traceback
import ipaddress
import rjsmin
import rcssmin
import minify_html
from scour import scour
from fourword.lib import FourWord
from fastapi import Response
from fastapi.responses import PlainTextResponse
from starlette.requests import Request, HTTPConnection
from starlette.types import Scope, ASGIApp, Receive, Send

from .config import Repositories, Hostnames, Files
from .renderer import render_error_page

class OptionManager:
    defaults = {
        "dev.nercone.options.apperance.theme": "dark"
    }

    def __init__(self, request: HTTPConnection):
        self.request = request

    def __contains__(self, key: str):
        return key in self.request.query_params or key in self.request.cookies

    def __len__(self):
        return len(self.request.cookies | self.request.query_params)

    def get(self, key: str, default: str | None = None):
        once = self.request.query_params.get(key + ".once", None)
        query = self.request.query_params.get(key, None)
        cookie = self.request.cookies.get(key, None)
        return once or query or cookie or default or self.defaults.get(key)

    def set(self, response: Response, key: str, value: str):
        response.set_cookie(key, value, samesite="lax")

    def apply(self, response: Response):
        queries = self.request.query_params
        cookies = self.request.cookies
        for key in queries:
            if not key.endswith(".once") and cookies.get(key) != queries.get(key) or self.defaults.get(key) != (queries[key] or cookies[key]):
                response.set_cookie(key, queries[key], samesite="lax")

class TrustManager:
    trusted_networks = [ipaddress.ip_network(network) for network in [
        "127.0.0.0/8",
        "169.254.0.0/16",

        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",

        "100.64.0.0/10",

        "::1/128",
        "fc00::/7",
        "fe80::/10"
    ]]

    def __init__(self, address: ipaddress.IPv4Address | ipaddress.IPv6Address):
        self.address = address

    @property
    def is_trusted(self) -> bool:
        return all([self.is_trusted_address])

    @property
    def is_trusted_address(self) -> bool:
        return any([self.address in network for network in self.trusted_networks])

class TimingManager:
    def __init__(self):
        self.timings: dict[str, list[float, float | None]] = {}

    def start(self, key: str) -> float:
        now = time.perf_counter()
        self.timings[key] = [now, None]
        return now

    def stop(self, key: str) -> float:
        now = time.perf_counter()
        self.timings[key] = [self.timings[key][0], now]
        return now

    @property
    def header(self) -> str:
        headers = []
        sorted_timings = sorted(self.timings.items(), key=lambda item: item[1][1] or float("inf"))
        for key, timing in sorted_timings:
            duration = round((timing[1] - timing[0]) * 1000, 3)
            headers.append(f"{key};dur={duration}")
        return ", ".join(headers)

class PPManager:
    defaults = {
        "camera": [],
        "microphone": [],
        "geolocation": [],
        "payment": [],
        "usb": [],
        "accelerometer": [],
        "gyroscope": [],
        "magnetometer": [],
        "display-capture": []
    }

    def __init__(self):
        self.directives: dict[str, list[str]] = dict(self.defaults)

    def set(self, key: str, value: list[str], override: bool = True):
        if override or key not in self.directives:
            self.directives[key] = value

    def append(self, key: str, *values: str):
        if key not in self.directives:
            self.directives[key] = list(values)
        else:
            self.directives[key] += list(values)

    def remove(self, key: str):
        self.directives.pop(key, None)

    @property
    def header(self) -> str:
        parts = []
        for key, value in self.directives.items():
            if value == ["*"]:
                parts.append(f"{key}=*")
            elif value:
                parts.append(f"{key}=({' '.join(value)})")
            else:
                parts.append(f"{key}=()")
        return ", ".join(parts)

class CSPManager:
    defaults = {
        "default-src": ["'self'", "assets.nercone.dev"],
        "script-src": ["'self'", "assets.nercone.dev"],
        "style-src": ["'self'", "assets.nercone.dev"],
        "font-src": ["'self'", "assets.nercone.dev"],
        "img-src": ["'self'", "assets.nercone.dev", "t3tra.dev", "drsb.f5.si", "data:"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'self'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "upgrade-insecure-requests": True
    }

    def __init__(self):
        self.directives: dict[str, list[str] | bool] = dict(self.defaults)

    def set(self, key: str, value: list[str] | bool, override: bool = True):
        if override or key not in self.directives:
            self.directives[key] = value

    def append(self, key: str, *values: str):
        if key not in self.directives:
            self.directives[key] = list(values)
        else:
            self.directives[key] += list(values)

    def remove(self, key: str):
        self.directives.pop(key, None)

    @property
    def header(self) -> str:
        parts = []
        for key, value in self.directives.items():
            if isinstance(value, bool) and value:
                parts.append(key)
            else:
                parts.append(f"{key} {' '.join(value)}")
        return "; ".join(parts).strip()

class Middleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        try:
            if scope["type"] not in ["http", "websocket"]:
                await self.app(scope, receive, send)
                return

            timings = TimingManager()
            timings.start("total")

            headers = dict(scope.get("headers", []))

            scope["id"] = FourWord()
            scope["trusted"] = TrustManager(ipaddress.ip_address(scope.get("client", ("", 0))[0]))
            scope["options"] = OptionManager(HTTPConnection(scope=scope))

            scope["pp"] = PPManager()
            scope["csp"] = CSPManager()

            hostname = headers.get(b"host", b"").decode().split(":")[0].strip()
            if hostname.split(".")[-1] == "localhost":
                subdomain = ".".join(hostname.split(".")[:-1])
            else:
                subdomain = ".".join(hostname.split(".")[:-2])

            if not scope["trusted"] and not any([hostname == candidate or hostname.endswith("." + candidate) for candidate in Hostnames.all]):
                response = PlainTextResponse("許可されていないホスト名でのアクセスです。", status_code=403)
                await self.send(response, scope, receive, send, timings)
                return

            if scope["type"] == "websocket":
                if subdomain not in ["", "www"]:
                    original_path = scope["path"] if scope["path"].strip() else "/"
                    subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"
                    scope = dict(scope, path=subdomain_path)
                await self.app(scope, receive, send)
                return

            timings.start("recieve")
            body = await self.read_body(receive)
            timings.stop("recieve")

            async def cached_receive():
                return {"type": "http.request", "body": body, "more_body": False}

            if subdomain in ["", "www"]:
                response = await self.get_response(scope, cached_receive, scope["path"], timings, "app")
                await self.send(response, scope, cached_receive, send, timings)

            else:
                original_path = scope["path"] if scope["path"].strip() else "/"
                subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"

                response = await self.get_response(scope, cached_receive, subdomain_path, timings, "app")
                if response.status_code < 400 or response.status_code >= 500:
                    await self.send(response, scope, cached_receive, send, timings)
                    return

                response = await self.get_response(scope, cached_receive, original_path, timings, "app-retry")
                await self.send(response, scope, cached_receive, send, timings)

        except Exception:
            try:
                try:
                    id_text = scope["id"].text
                except Exception:
                    id_text = "NOTSET"

                with Files.Logs.error.open("a", encoding="utf-8") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(f"[{id_text}]\n{traceback.format_exc()}\n")

                return render_error_page(Request(scope=scope, receive=receive), status_code=500)
            except Exception:
                return PlainTextResponse("Internal Server Error", status_code=500)

    async def get_response(self, scope: Scope, receive: Receive, path: str, timings: TimingManager, key: str) -> Response:
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        new_scope = dict(scope, path=path)

        status_code = 200
        resp_headers = []
        body_parts = []

        async def capture_send(message):
            nonlocal status_code, resp_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                resp_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        timings.start(key)
        await self.app(new_scope, receive, capture_send)
        timings.stop(key)

        response = Response(content=b"".join(body_parts), status_code=status_code)

        for k, v in resp_headers:
            response.headers.raw.append((k, v))

        return response

    async def read_body(self, receive: Receive) -> bytes:
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        return body

    async def send(self, response: Response, scope, receive, send, timings: TimingManager):
        content_type = response.headers.get("content-type", "")

        if "text/html" in content_type:
            timings.start("minify")
            try:
                response.body = minify_html.minify(response.body.decode("utf-8", errors="replace"), minify_js=True, minify_css=True, keep_comments=True).encode("utf-8")
            except Exception:
                pass
            timings.stop("minify")

        elif "text/css" in content_type:
            timings.start("minify")
            try:
                response.body = rcssmin.cssmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            timings.stop("minify")

        elif any(content_type.startswith(t) for t in ["text/javascript", "application/javascript"]):
            timings.start("minify")
            try:
                response.body = rjsmin.jsmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            timings.stop("minify")

        elif "image/svg" in content_type:
            timings.start("minify")
            try:
                scour_options = scour.generateDefaultOptions()
                scour_options.newlines = False
                scour_options.shorten_ids = True
                scour_options.strip_comments = True
                response.body = scour.scourString(response.body.decode("utf-8", errors="replace"), scour_options).encode("utf-8")
            except Exception:
                pass
            timings.stop("minify")

        def set_header(key: str, value: str, override: bool = True):
            if override or key.lower() not in response.headers:
                response.headers[key.lower()] = value

        set_header("Content-Length", str(len(response.body)))

        set_header("X-Request-Id", scope["id"].text)

        set_header("Server", f"nercone.dev ({Repositories.Server.version}+{Repositories.Contents.version})")
        set_header("Onion-Location", f"http://{Hostnames.onion[0]}{scope.get("path", "/")}" + (f"?{scope.get("query_string", b"").decode()}" if scope.get("query_string", b"").decode() else ""))
        set_header("Link", "<https://nercone.dev/sitemap.xml>; rel=\"sitemap\", <https://nercone.dev/robots.txt>; rel=\"robots\"")

        set_header("Cache-Control", "no-cache", override=False)

        set_header("Access-Control-Allow-Origin", "*", override=False)
        set_header("Access-Control-Allow-Methods", "*", override=False)
        set_header("Access-Control-Allow-Headers", "*", override=False)

        set_header("Referrer-Policy", "strict-origin-when-cross-origin")
        set_header("Permissions-Policy", scope["pp"].header)
        set_header("Content-Security-Policy", scope["csp"].header)

        timings.stop("total")
        set_header("Server-Timing", timings.header)

        await response(scope, receive, send)
