import io
import re
import yaml
import hashlib
import mistune
import resvg_py
from typing import Any
from html import escape
from http import HTTPStatus
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse, FileResponse, RedirectResponse

from .resolver import resolve_file, resolve_page, resolve_shorturl
from .constants import Directories
from .templates import templates, access_counter

class CustomHTMLRenderer(mistune.HTMLRenderer):
    _alert_re = re.compile(r'^\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\n(.*?))?</p>\s*', re.IGNORECASE | re.DOTALL,)

    def block_code(self, code, **attrs):
        return f'<pre>{mistune.escape(code)}</pre>\n'

    def block_quote(self, text):
        m = self._alert_re.match(text)
        if m:
            alert_type = m.group(1).upper()
            inline_content = m.group(2)
            rest = text[m.end():]
            label = alert_type.capitalize()
            css_class = alert_type.lower()
            inner = (f'<p>{inline_content}</p>\n' if inline_content and inline_content.strip() else '') + rest
            return f'<div class="block block-{css_class}">\n<b>{label}</b>\n{inner}</div>\n'
        return f'<blockquote>\n{text}</blockquote>\n'

markitdown = MarkItDown()
htmlitdown = mistune.create_markdown(renderer=CustomHTMLRenderer(escape=False), plugins=["table", "strikethrough", "task_lists", "footnotes"])

def default_response(path: str, request: Request, status_code: int = 200, count: bool = True, render: bool = True, context: dict[str, Any] = {}, headers: dict[str, str] = {}):
    context.update(request.scope)

    markdown_ua = ["curl", "claude-user", "chatgpt-user", "google-extended", "perplexity-user"]
    markdown_mode = any([path.endswith(".md"), "text/markdown" in request.headers.get("accept", "").lower(), any([ua in request.headers.get("user-agent", "").lower() for ua in markdown_ua])])

    try:
        if page := resolve_page(path, markdown_mode=markdown_mode):
            with Directories.public.joinpath(page).open("r") as f:
                source = f.read()

            if render:
                if not source.startswith("---"):
                    front = {}
                    body = source
                else:
                    end = source.find("\n---", 3)
                    if end == -1:
                        front = {}
                        body = source
                    else:
                        front = yaml.safe_load(source[3:end]) or {}
                        body = source[end+4:].lstrip("\n")

                if page.endswith(".html"):
                    html = templates.env.from_string(body).render(request=request, **context)
                elif page.endswith(".md"):
                    html = htmlitdown(templates.env.from_string(body).render(request=request, **context))

                if "base" in front:
                    source = f"{{% extends \"{front['base']}\" %}}\n"
                else:
                    source = "{% extends \"/base.html\" %}\n"
                for key, value in front.items():
                    source += f"{{% block {key} %}}{value}{{% endblock %}}\n"
                source += f"{{% block main %}}\n{html}\n{{% endblock %}}\n"

                content = templates.env.from_string(source).render(request=request, **context)
                response = PlainTextResponse(content, status_code=status_code, media_type="text/html")

                if markdown_mode:
                    soup = BeautifulSoup(content, "html.parser")
                    main = str(soup.find("main")) if soup.find("main") else content
                    content = markitdown.convert_stream(io.BytesIO(main.encode("utf-8")), file_extension=".html").text_content
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/markdown")
            else:
                content = source
                if page.endswith(".html"):
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/html")
                elif page.endswith(".md"):
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/markdown")

            etag = '"' + hashlib.sha256(content.encode("utf-8")).hexdigest() + '"'
            if request.headers.get("if-none-match") == etag:
                response = Response(status_code=304, headers={"ETag": etag})
            else:
                response.headers["ETag"] = etag

            if count:
                access_counter.increase()

        elif file := resolve_file(path):
            etag = '"' + hashlib.sha256(file.read_bytes()).hexdigest() + '"'
            if request.headers.get("if-none-match") == etag:
                response = Response(status_code=304, headers={"ETag": etag})
            else:
                response = FileResponse(file, status_code=status_code, headers={"ETag": etag})

        elif url := resolve_shorturl(path):
            response = RedirectResponse(url, status_code=status_code if 299 < status_code < 400 else 307)

        else:
            response = render_error_page(request, 404, "リクエストしたページは現在ご利用になれません。削除/移動されたか、URLが間違っている可能性があります。", "そんなページ知らないっ！")

    except PermissionError:
        response = render_error_page(request, 403, "何をしてるんです？脆弱性報告のためならいいのですが、データ盗んで悪用するためなら今すぐにやめてくださいね？", "ディレクトリトラバーサルね、知ってる。公開してないところ覗きたいの？えっt")

    for key, value in headers.items():
        response.headers[key.lower().strip()] = value

    context["options"].apply(response)

    return response

error_messages = {
    400: {"normal": "リクエストの構文が正しくないか、パラメータが不正です。", "joke": "日本語でおk"},
    401: {"normal": "このリソースにアクセスするには認証が必要です。", "joke": "見たいのならログインすることね"},
    402: {"normal": "このリソースへのアクセスには支払いが必要です。", "joke": "夢が欲しけりゃ金払え！"},
    403: {"normal": "このリソースへのアクセス権がありません。", "joke": "あんたなんかに見せるもんですか！"},
    404: {"normal": "リクエストしたページまたはリソースが見つかりません。", "joke": "そんなページ知らないっ！"},
    405: {"normal": "このリソースではそのHTTPメソッドは許可されていません。", "joke": "そのMethodはNot Allowedだよ"},
    406: {"normal": "リクエストのAcceptヘッダーと一致するレスポンスを生成できません。", "joke": "すまんがその条件ではお渡しできない。"},
    407: {"normal": "このリソースにアクセスするにはプロキシの認証が必要です。", "joke": "うちのプロキシ使うんだったらまずログインしな。"},
    408: {"normal": "リクエストが時間内に完了しませんでした。", "joke": "もう用がないならさっさと帰りなさい。"},
    409: {"normal": "現在のリソースの状態とリクエストが競合しています。", "joke": "ちょっと待ったそんな話聞いてないぞ"},
    410: {"normal": "リクエストしたリソースは恒久的に削除されました。", "joke": "もう無いで。"},
    411: {"normal": "リクエストにはContent-Lengthヘッダーが必要です。", "joke": "サイズを教えろ。話はそれからだ。"},
    412: {"normal": "リクエストの前提条件がサーバーの状態と一致しません。", "joke": "なにその条件美味しいの"},
    413: {"normal": "リクエストのボディがサーバーの許容サイズを超えています。", "joke": "そ、そそ、そんなの入りきらないよっ！"},
    414: {"normal": "リクエストURIがサーバーの処理できる長さを超えています。", "joke": "もちつけ"},
    415: {"normal": "リクエストのメディア形式はサポートされていません。", "joke": "そんな形式知らない！"},
    416: {"normal": "リクエストしたレンジはリソースのサイズ内に存在しません。", "joke": "ちっさぁ:heart:"},
    417: {"normal": "リクエストのExpectヘッダーの要件をサーバーが満たせません。", "joke": "期待させて悪かったわね！"},
    418: {"normal": "このサーバーはティーポットです。コーヒーを淹れることはできません。", "joke": "ティーポット「私はコーヒーを注ぐためのものではありません！やだっ！」"},
    421: {"normal": "リクエストが意図しないサーバーに到達しました。", "joke": "またあいつ案内先間違えてるよ...どうしよ..."},
    426: {"normal": "このリクエストを処理するにはプロトコルのアップグレードが必要です。", "joke": "それに答えるには、まずWebSocketに移動したい。"}
}

def render_error_page(request: Request, status_code: int = 500, message: str | None = None, joke_message: str | None = None) -> Response:
    if status_code in [502, 503, 504]:
        request.scope["csp"].append("script-src", "'unsafe-inline'")
        request.scope["csp"].append("style-src", "fonts.googleapis.com", "'unsafe-inline'")
        request.scope["csp"].append("font-src", "fonts.gstatic.com")
        return default_response("error/nginx", request=request, status_code=status_code, count=False, render=False)
    elif status_code in range(500, 599):
        request.scope["csp"].append("script-src", "'unsafe-inline'")
        request.scope["csp"].append("style-src", "fonts.googleapis.com", "'unsafe-inline'")
        request.scope["csp"].append("font-src", "fonts.gstatic.com")
        return default_response("error/server", request=request, status_code=status_code, count=False, render=False)
    else:
        context = {
            "status_code": status_code,
            "status_code_name": HTTPStatus(status_code).phrase,
            "message": message or error_messages.get(status_code, {}).get("normal", "不明なエラーが発生しました。"),
            "joke_message": joke_message or error_messages.get(status_code, {}).get("joke", "あんのーん")
        }
        return default_response("error/client", request=request, status_code=status_code, count=False, context=context)

thumbnail_font_dir = Directories.public.joinpath("assets", "fonts")
thumbnail_font_files = [
    str(thumbnail_font_dir / "NerconeSansJP-Regular.ttf"),
    str(thumbnail_font_dir / "NerconeSansJP-Italic.ttf"),
    str(thumbnail_font_dir / "NerconeSansJP-Bold.ttf"),
    str(thumbnail_font_dir / "NerconeSansJP-BoldItalic.ttf"),
    str(thumbnail_font_dir / "NerconeMonoJP-Regular.ttf"),
    str(thumbnail_font_dir / "NerconeMonoJP-Italic.ttf"),
    str(thumbnail_font_dir / "NerconeMonoJP-Bold.ttf"),
    str(thumbnail_font_dir / "NerconeMonoJP-BoldItalic.ttf")
]

def render_thumbnail_svg(path: str = "/", title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> str:
    if file := resolve_file(f"/assets/images/thumbnail/template/{template}.svg"):
        parts = [p for p in path.strip("/").split("/") if p]
        svg = file.read_text(encoding="utf-8")
        svg = svg.replace("__PATH__", escape("nercone.dev/" + "/".join(parts) if parts else "nercone.dev"))
        svg = svg.replace("__TITLE__", escape(title))
        svg = svg.replace("__DESCRIPTION__", escape(description))
        return svg
    else:
        raise FileNotFoundError()

def render_thumbnail_png(path: str = "/", title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> bytes:
    svg = render_thumbnail_svg(path=path, title=title, description=description, template=template)
    png = resvg_py.svg_to_bytes(svg, font_files=thumbnail_font_files, width=1280, height=640)
    return png
