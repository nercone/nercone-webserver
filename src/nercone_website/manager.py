import time
import ipaddress
from fastapi import Response
from starlette.requests import Request, HTTPConnection
from .constants import reserved_cookie_keys

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

class NetworkManager:
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

    def __init__(self, address: ipaddress.IPv4Address | ipaddress.IPv6Address | None, host: str | None, port: int | None):
        self.address = address
        self.host = host
        self.port = port

    @property
    def trusted(self) -> bool:
        if self.address is None:
            return False
        return any(self.address in network for network in self.trusted_networks)

class OptionManager:
    defaults = {
        "dev.nercone.options.apperance.theme": "dark"
    }

    def __init__(self, request: HTTPConnection | Request):
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
            if key.lower() in reserved_cookie_keys:
                continue
            if not key.endswith(".once") and cookies.get(key) != queries.get(key) or self.defaults.get(key) != (queries[key] or cookies[key]):
                response.set_cookie(key, queries[key], samesite="lax")
