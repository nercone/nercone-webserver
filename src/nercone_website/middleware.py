import time
import rjsmin
import rcssmin
from scour import scour
from fastapi import Response
from fastapi.responses import PlainTextResponse
from starlette.types import Scope, ASGIApp, Receive, Send

from .logger import log_access, finalize_log
from .config import Hostnames, AccessSources, Options

class Middleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        hostname = headers.get(b"host", b"").decode().split(":")[0].strip()

        hostname_parts = hostname.split(".")
        if hostname_parts[1:] == ["localhost"]:
            subdomain = ".".join(hostname_parts[:-1])
        else:
            subdomain = ".".join(hostname_parts[:-2])

        if scope["type"] == "websocket":
            if subdomain not in ["", "www"]:
                original_path = scope["path"] if scope["path"].strip() else "/"
                subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"
                scope = dict(scope, path=subdomain_path)
            await self.app(scope, receive, send)
            return

        timings: dict[str, float] = {}
        request_start = time.perf_counter()

        scope["log"] = log_access(scope)
        scope["trusted"] = AccessSources.is_trusted(scope.get("client", ("", 0))[0], headers.get(b"x-forwarded-for", b"").decode())

        if not scope["trusted"] and not any([hostname == candidate or hostname.endswith("." + candidate) for candidate in Hostnames.all]):
            response = PlainTextResponse("許可されていないホスト名でのアクセスです。", status_code=400)
            await self._send(response, scope, receive, send, timings, request_start)
            finalize_log(scope["log"], response.status_code, request_start, timings)
            return

        recv_start = time.perf_counter()
        body = await self._read_body(receive)
        timings["recv"] = (time.perf_counter() - recv_start) * 1000

        async def cached_receive():
            return {"type": "http.request", "body": body, "more_body": False}

        if subdomain not in ["", "www"]:
            original_path = scope["path"] if scope["path"].strip() else "/"
            subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"

            response = await self._get_response(scope, cached_receive, subdomain_path, timings, "app")
            if response.status_code < 400 or response.status_code >= 500:
                await self._send(response, scope, cached_receive, send, timings, request_start)
                finalize_log(scope["log"], response.status_code, request_start, timings)
                return

            response = await self._get_response(scope, cached_receive, original_path, timings, "app-retry")
            await self._send(response, scope, cached_receive, send, timings, request_start)
            finalize_log(scope["log"], response.status_code, request_start, timings)
        else:
            response = await self._get_response(scope, cached_receive, scope["path"], timings, "app")
            await self._send(response, scope, cached_receive, send, timings, request_start)
            finalize_log(scope["log"], response.status_code, request_start, timings)

    async def _get_response(self, scope: Scope, receive: Receive, path: str, timings: dict, key: str) -> Response:
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

        app_start = time.perf_counter()
        await self.app(new_scope, receive, capture_send)
        timings[key] = timings.get(key, 0.0) + (time.perf_counter() - app_start) * 1000

        response = Response(
            content=b"".join(body_parts),
            status_code=status_code,
        )

        if response.status_code == 404 and path != "/" and path.endswith("/"):
            return await self._get_response(scope, receive, path.rstrip("/"), timings, key)

        for k, v in resp_headers:
            response.headers.raw.append((k, v))

        return response

    async def _read_body(self, receive: Receive) -> bytes:
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        return body

    async def _send(self, response: Response, scope, receive, send, timings: dict, request_start: float):
        content_type = response.headers.get("content-type", "")

        if "text/css" in content_type:
            minify_start = time.perf_counter()
            try:
                response.body = rcssmin.cssmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            timings["minify"] = timings.get("minify", 0.0) + (time.perf_counter() - minify_start) * 1000

        elif any(content_type.startswith(t) for t in ["text/javascript", "application/javascript"]):
            minify_start = time.perf_counter()
            try:
                response.body = rjsmin.jsmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            timings["minify"] = timings.get("minify", 0.0) + (time.perf_counter() - minify_start) * 1000

        elif "image/svg" in content_type:
            minify_start = time.perf_counter()
            try:
                response.body = scour.scourString(response.body.decode("utf-8", errors="replace"), Options.scour_options).encode("utf-8")
            except Exception:
                pass
            timings["minify"] = timings.get("minify", 0.0) + (time.perf_counter() - minify_start) * 1000

        def set_header(key: str, value: str, override: bool = True):
            if override or key.lower() not in response.headers:
                response.headers[key.lower()] = value

        set_header("Content-Length", str(len(response.body)))

        if content_type.startswith("text/html"):
            set_header("Cache-Control", "no-cache", override=False)
        else:
            set_header("Cache-Control", "public, max-age=604800", override=False)

        for header in Options.headers:
            set_header(header["key"], header["value"], override=header["override"])

        timings["total"] = (time.perf_counter() - request_start) * 1000
        timings_header = ", ".join([f"{name};dur={round(value, 3)}" for name, value in timings.items()])
        if "Server-Timing" in response.headers:
            timings_header = response.headers.get("Server-Timing", "").strip() + ", " + timings_header
        set_header("Server-Timing", timings_header)

        await response(scope, receive, send)
