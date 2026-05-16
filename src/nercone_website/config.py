import os
import ipaddress
import subprocess
from scour import scour
from pathlib import Path
from fastapi import Request, Response

class Directories:
    base = Path.cwd()
    public = base.joinpath("public")
    logs = base.joinpath("logs")
    databases = base.joinpath("databases")

class Files:
    quotes = Directories.public.joinpath("quotes.txt")
    shorturls = Directories.public.joinpath("shorturls.json")
    error = Directories.public.joinpath("error", "index.html")
    access_counter = Directories.databases.joinpath("access_counter.txt")

    class Logs:
        error = Directories.logs.joinpath("error.log")

    class Cache:
        google_fonts = Directories.databases.joinpath("google_fonts.json")

class Repositories:
    class Server:
        url = subprocess.run(["/usr/bin/git", "remote", "get-url", "origin"], text=True, capture_output=True, cwd=Directories.base).stdout.strip()
        version = subprocess.run(["/usr/bin/git", "rev-parse", "--short", "HEAD"], text=True, capture_output=True, cwd=Directories.base).stdout.strip()

    class Contents:
        url = subprocess.run(["/usr/bin/git", "remote", "get-url", "origin"], text=True, capture_output=True, cwd=Directories.public).stdout.strip()
        version = subprocess.run(["/usr/bin/git", "rev-parse", "--short", "HEAD"], text=True, capture_output=True, cwd=Directories.public).stdout.strip()

class ErrorMessages:
    normal = {
        400: "リクエストの構文が正しくないか、パラメータが不正です。",
        401: "このリソースにアクセスするには認証が必要です。",
        402: "このリソースへのアクセスには支払いが必要です。",
        403: "このリソースへのアクセス権がありません。",
        404: "リクエストしたページまたはリソースが見つかりません。",
        405: "このリソースではそのHTTPメソッドは許可されていません。",
        406: "リクエストのAcceptヘッダーと一致するレスポンスを生成できません。",
        407: "このリソースにアクセスするにはプロキシの認証が必要です。",
        408: "リクエストが時間内に完了しませんでした。",
        409: "現在のリソースの状態とリクエストが競合しています。",
        410: "リクエストしたリソースは恒久的に削除されました。",
        411: "リクエストにはContent-Lengthヘッダーが必要です。",
        412: "リクエストの前提条件がサーバーの状態と一致しません。",
        413: "リクエストのボディがサーバーの許容サイズを超えています。",
        414: "リクエストURIがサーバーの処理できる長さを超えています。",
        415: "リクエストのメディア形式はサポートされていません。",
        416: "リクエストしたレンジはリソースのサイズ内に存在しません。",
        417: "リクエストのExpectヘッダーの要件をサーバーが満たせません。",
        418: "このサーバーはティーポットです。コーヒーを淹れることはできません。",
        421: "リクエストが意図しないサーバーに到達しました。",
        426: "このリクエストを処理するにはプロトコルのアップグレードが必要です。",
    }

    joke = {
        400: "日本語でおk",
        401: "見たいのならログインすることね",
        402: "夢が欲しけりゃ金払え！",
        403: "あんたなんかに見せるもんですか！",
        404: "そんなページ知らないっ！",
        405: "そのMethodはNot Allowedだよ",
        406: "すまんがその条件ではお渡しできない。",
        407: "うちのプロキシ使うんだったらまずログインしな。",
        408: "もう用がないならさっさと帰りなさい。",
        409: "ちょっと待ったそんな話聞いてないぞ",
        410: "もう無いで。",
        411: "サイズを教えろ。話はそれからだ。",
        412: "なにその条件美味しいの",
        413: "そ、そそ、そんなの入りきらないよっ！",
        414: "もちつけ",
        415: "そんな形式知らない！",
        416: "ちっさぁ:heart:",
        417: "期待させて悪かったわね！",
        418: "ティーポット「私はコーヒーを注ぐためのものではありません！やだっ！」",
        421: "またあいつ案内先間違えてるよ...どうしよ...",
        426: "それに答えるには、まずWebSocketに移動したい。"
    }

class Hostnames:
    local = ["localhost", "127.0.0.1"]
    public = ["nercone.dev", "nerc1.dev", "diamondgotcat.net", "d-g-c.net"]
    onion = "4sbb7xhdn4meuesnqvcreewk6sjnvchrsx4lpnxmnjhz2soat74finid.onion"
    all = local + public + [onion]

class AccessSources:
    trusted = [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",

        "::1/128",
        "fc00::/7",
        "fe80::/10",

        "100.64.0.0/10"
    ]
    networks = [ipaddress.ip_network(n) for n in trusted]

    @staticmethod
    def is_trusted(ip: str, forwarded_for: str = "") -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            ip_is_trusted = any(addr in net for net in AccessSources.networks)
        except ValueError:
            return False

        if not ip_is_trusted:
            return False

        if forwarded_for:
            entries = [e.strip() for e in forwarded_for.split(",")]

            proxy_idx = None
            for i in range(len(entries) - 1, -1, -1):
                try:
                    if entries[i] and ipaddress.ip_address(entries[i]) == addr:
                        proxy_idx = i
                        break
                except ValueError:
                    continue

            if proxy_idx is None:
                return True

            if proxy_idx == 0:
                return True

            effective_entry = entries[proxy_idx - 1]
            if not effective_entry:
                return True
            try:
                effective_addr = ipaddress.ip_address(effective_entry)
                return any(effective_addr in net for net in AccessSources.networks)
            except ValueError:
                return False

        return True

class Options:
    database_url = os.environ.get("DATABASE_URL", "postgresql://website:website@localhost:5432/website")

    scour_options = scour.generateDefaultOptions()
    scour_options.newlines = False
    scour_options.shorten_ids = True
    scour_options.strip_comments = True

class UserOptions:
    defaults = {
        "dev.nercone.useroptions.apperance.theme": "dark"
    }

    def __init__(self, request: Request):
        self.request = request

    def __contains__(self, key: str):
        return key in self.request.query_params or key in self.request.cookies

    def __len__(self):
        return len(self.request.cookies | self.request.query_params)

    def get(self, key: str, default: str | None = None):
        query = self.request.query_params.get(key, None)
        cookie = self.request.cookies.get(key, None)
        return query or cookie or default or self.defaults.get(key)

    def apply(self, response: Response):
        queries = self.request.query_params
        cookies = self.request.cookies
        for key in queries:
            if cookies.get(key) != queries.get(key) or self.defaults.get(key) != (queries[key] or cookies[key]):
                response.set_cookie(key, queries[key], samesite="lax")
