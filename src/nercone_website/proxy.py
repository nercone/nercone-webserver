import time
import httpx
import asyncio
from websockets.client import connect
from fastapi import Request, Response, WebSocket

hop_by_hop_headers = ["transfer-encoding", "connection", "keep-alive", "upgrade", "proxy-authenticate", "proxy-authorization", "te", "trailers", "content-encoding", "content-length"]

def _prefix_server_timing(value: str, prefix: str) -> str:
    parts = []
    for entry in value.split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, sep, params = entry.partition(";")
        name = name.strip()
        if not name:
            continue
        renamed = f"{prefix}-{name}"
        parts.append(renamed + (sep + params if sep else ""))
    return ", ".join(parts)

def make_http_proxy(base_url_http: str, headers: dict = {}, remove_prefix_path: bool = False):
    async def http_proxy(request: Request, path: str = "") -> Response:
        url = f"{base_url_http}/{path}" if remove_prefix_path else f"{base_url_http}{request.url.path}"
        merged_headers = dict(request.headers)
        merged_headers.pop("accept-encoding", None)
        merged_headers |= {k.lower(): v for k, v in headers.items()}
        raw_headers = [(k.encode("latin-1"), v.encode("latin-1")) for k, v in merged_headers.items()]
        async with httpx.AsyncClient() as client:
            upstream_start = time.perf_counter()
            resp = await client.request(
                method=request.method,
                url=url,
                headers=raw_headers,
                content=await request.body(),
                params=request.query_params
            )
            upstream_dur_ms = (time.perf_counter() - upstream_start) * 1000
        response = Response(content=resp.content, status_code=resp.status_code)
        for k, v in resp.headers.multi_items():
            if k.lower() in hop_by_hop_headers:
                continue
            if k.lower() == "server-timing":
                continue
            response.headers.append(k, v)

        timing_parts = [f"upstream;dur={round(upstream_dur_ms, 3)}"]
        for k, v in resp.headers.multi_items():
            if k.lower() == "server-timing" and v.strip():
                prefixed = _prefix_server_timing(v, "upstream")
                if prefixed:
                    timing_parts.append(prefixed)
        response.headers["Server-Timing"] = ", ".join(timing_parts)
        return response
    return http_proxy

def make_websocket_proxy(base_url_websocket: str, remove_prefix_path: bool = False):
    async def websocket_proxy(client_ws: WebSocket, path: str = ""):
        url = f"{base_url_websocket}/{path}" if remove_prefix_path else f"{base_url_websocket}{client_ws.url.path}"
        await client_ws.accept()
        async with connect(url) as server_ws:
            async def client_to_server():
                async for message in client_ws.iter_bytes():
                    await server_ws.send(message)
            async def server_to_client():
                async for message in server_ws:
                    await client_ws.send_bytes(message)
            try:
                await asyncio.gather(
                    asyncio.create_task(client_to_server()),
                    asyncio.create_task(server_to_client()),
                    return_exceptions=True
                )
            finally:
                if not client_ws.client_state.value == 3:
                    await client_ws.close()
    return websocket_proxy
