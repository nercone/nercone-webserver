import traceback
import ipaddress
from fourword.lib import FourWord
from fastapi import Response
from fastapi.responses import PlainTextResponse
from starlette.requests import Request, HTTPConnection
from starlette.types import ASGIApp, Scope, Receive, Send

import rjsmin
import rcssmin
import minify_html
from scour import scour

from .logger import Logger
from .manager import PPManager, CSPManager, TimingManager, NetworkManager, OptionManager
from .renderer import render_error_page
from .constants import Repositories, Hostnames, unix_socket

class Middleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        try:
            if scope["type"] not in ["http", "websocket"]:
                await self.app(scope, receive, send)
                return

            headers = dict(scope.get("headers", []))

            scope.update({
                "id": FourWord(),
                "pp": PPManager(),
                "csp": CSPManager(),
                "timings": TimingManager(),
                "network": NetworkManager(
                    address = None if unix_socket else ipaddress.ip_address(scope["client"][0]),
                    host = headers.get(b"x-real-ip", b"UDS") if unix_socket else scope["client"][0],
                    port = 0 if unix_socket else scope["client"][1]
                ),
                "options": OptionManager(HTTPConnection(scope=scope))
            })

            scope["timings"].start("total")

            hostname = headers.get(b"host", b"").decode().split(":")[0].strip()
            if hostname.split(".")[-1] == "localhost":
                subdomain = ".".join(hostname.split(".")[:-1])
            else:
                subdomain = ".".join(hostname.split(".")[:-2])

            if not scope["network"].trusted and not any([hostname == candidate or hostname.endswith("." + candidate) for candidate in Hostnames.public]):
                response = PlainTextResponse("許可されていないホスト名でのアクセスです。", status_code=403)
                await self.send(response, scope, receive, send)
                return

            if scope["type"] == "websocket":
                if subdomain not in ["", "www"]:
                    original_path = scope["path"] if scope["path"].strip() else "/"
                    subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"
                    scope = dict(scope, path=subdomain_path)
                await self.app(scope, receive, send)
                return

            if scope.get("method") == "OPTIONS":
                response = Response(status_code=204)
                await self.send(response, scope, receive, send)
                return

            scope["timings"].start("recieve")
            body = await self.read_body(receive)
            scope["timings"].stop("recieve")

            async def cached_receive():
                return {"type": "http.request", "body": body, "more_body": False}

            if subdomain in ["", "www"]:
                response = await self.get_response(scope, cached_receive, scope["path"], "app")
                await self.send(response, scope, cached_receive, send)

            else:
                original_path = scope["path"] if scope["path"].strip() else "/"
                subdomain_path = f"/{'/'.join(subdomain.split('.')[::-1])}{original_path}"

                response = await self.get_response(scope, cached_receive, subdomain_path, "app")
                if response.status_code < 400 or response.status_code >= 500:
                    await self.send(response, scope, cached_receive, send)
                    return

                response = await self.get_response(scope, cached_receive, original_path, "app-retry")
                await self.send(response, scope, cached_receive, send)

        except Exception:
            try:
                Logger.log_error(scope.get("id", FourWord()).text, traceback.format_exc())
                return render_error_page(Request(scope=scope, receive=receive), status_code=500)
            except Exception:
                return PlainTextResponse("Internal Server Error", status_code=500)

    async def get_response(self, scope: Scope, receive: Receive, path: str, key: str) -> Response:
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

        scope["timings"].start(key)
        await self.app(new_scope, receive, capture_send)
        scope["timings"].stop(key)

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

    async def send(self, response: Response, scope, receive, send):
        content_type = response.headers.get("content-type", "")

        if "text/html" in content_type:
            scope["timings"].start("minify")
            try:
                response.body = minify_html.minify(response.body.decode("utf-8", errors="replace"), minify_js=True, minify_css=True, keep_comments=True).encode("utf-8")
            except Exception:
                pass
            scope["timings"].stop("minify")

        elif "text/css" in content_type:
            scope["timings"].start("minify")
            try:
                response.body = rcssmin.cssmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            scope["timings"].stop("minify")

        elif any(content_type.startswith(t) for t in ["text/javascript", "application/javascript"]):
            scope["timings"].start("minify")
            try:
                response.body = rjsmin.jsmin(response.body.decode("utf-8", errors="replace")).encode("utf-8")
            except Exception:
                pass
            scope["timings"].stop("minify")

        elif "image/svg" in content_type:
            scope["timings"].start("minify")
            try:
                scour_options = scour.generateDefaultOptions()
                scour_options.newlines = False
                scour_options.shorten_ids = True
                scour_options.strip_comments = True
                response.body = scour.scourString(response.body.decode("utf-8", errors="replace"), scour_options).encode("utf-8")
            except Exception:
                pass
            scope["timings"].stop("minify")

        def set_header(key: str, value: str, override: bool = True):
            if override or key.lower() not in response.headers:
                response.headers[key.lower()] = value

        set_header("Content-Length", str(len(response.body)))

        set_header("X-Request-Id", scope["id"].text)

        set_header("Server", f"nercone.dev ({Repositories.Server.version}+{Repositories.Contents.version})")
        set_header("Onion-Location", f"http://{Hostnames.tor[0]}{scope.get("path", "/")}" + (f"?{scope.get("query_string", b"").decode()}" if scope.get("query_string", b"").decode() else ""))
        set_header("Link", "<https://nercone.dev/sitemap.xml>; rel=\"sitemap\", <https://nercone.dev/robots.txt>; rel=\"robots\"")

        set_header("Cache-Control", "no-cache", override=False)

        set_header("Referrer-Policy", "strict-origin-when-cross-origin")
        set_header("Permissions-Policy", scope["pp"].header)
        set_header("Content-Security-Policy", scope["csp"].header)

        if content_type.startswith(("font/", "image/", "text/css", "text/javascript", "application/javascript")):
            set_header("Access-Control-Allow-Origin", "*", override=False)

        else:
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode().strip()
            origin_host = origin.removeprefix("https://").removeprefix("http://").split("/")[0].split(":")[0]

            if any(origin_host == candidate or origin_host.endswith("." + candidate) for candidate in Hostnames.all):
                vary = response.headers.get("vary", "") + ", Origin" if "vary" in response.headers else "Origin"
                set_header("Vary", vary)

                set_header("Access-Control-Allow-Origin", origin, override=False)
                set_header("Access-Control-Allow-Credentials", "true", override=False)

                if scope.get("method") == "OPTIONS":
                    set_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS", override=False)
                    set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With", override=False)
                    set_header("Access-Control-Max-Age", "86400", override=False)

        scope["timings"].stop("total")
        set_header("Server-Timing", scope["timings"].header)

        Logger.log_access(request=Request(scope=scope, receive=receive), response=response)
        await response(scope, receive, send)
