import io
import re
import json
import yaml
import hashlib
import mistune
import resvg_py
from typing import Any
from html import escape
from pathlib import Path
from http import HTTPStatus
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from starlette.templating import Jinja2Templates
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse, FileResponse, RedirectResponse

from .config import Directories, Files, ErrorMessages
from .database import AccessCounter

markitdown = MarkItDown()

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
htmlitdown = mistune.create_markdown(renderer=CustomHTMLRenderer(escape=False), plugins=["table", "strikethrough", "task_lists", "footnotes"])

def resolve_file(path: str) -> Path | None:
    path = Directories.public.joinpath(path.lstrip("/")).resolve()
    if not path.is_relative_to(Directories.public):
        raise PermissionError()
    return path if path.is_file() else None

def resolve_page(path: str) -> str | None:
    if path in ["", "/"]:
        template_candidates = ["index.html", "README.html"]
        markdown_candidates = ["index.md",   "README.md"]
    elif path.endswith(".html"):
        template_candidates = [f"{path[:-5].strip('/')}.html", f"{path[:-5].strip('/')}/index.html", f"{path[:-5].strip('/')}/README.html"]
        markdown_candidates = [f"{path[:-5].strip('/')}.md",   f"{path[:-5].strip('/')}/index.md",   f"{path[:-5].strip('/')}/README.md"]
    elif path.endswith(".md"):
        template_candidates = [f"{path[:-3].strip('/')}.html", f"{path[:-3].strip('/')}/index.html", f"{path[:-3].strip('/')}/README.html"]
        markdown_candidates = [f"{path[:-3].strip('/')}.md",   f"{path[:-3].strip('/')}/index.md",   f"{path[:-3].strip('/')}/README.md"]
    else:
        template_candidates = [f"{path.strip('/')}.html", f"{path.strip('/')}/index.html", f"{path.strip('/')}/README.html"]
        markdown_candidates = [f"{path.strip('/')}.md",   f"{path.strip('/')}/index.md",   f"{path.strip('/')}/README.md"]

    candidates = template_candidates + markdown_candidates

    for candidate in candidates:
        if file := resolve_file(candidate):
            return str(file.relative_to(Directories.public))

    return None

def resolve_shorturl(path: str) -> str | None:
    max_retry = 10

    if Files.shorturls.is_file():
        with Files.shorturls.open("r", encoding="utf-8") as f:
            shorturls = json.load(f)

        current = path.strip("/")
        visited = set()

        for _ in range(max_retry):
            if current in visited or current not in shorturls:
                return None
            visited.add(current)

            entry = shorturls[current]
            if entry["type"] == "redirect":
                return entry["content"]
            elif entry["type"] == "alias":
                current = entry["content"]

    return None

def render(path: str, request: Request, templates: Jinja2Templates, access_counter: AccessCounter | None = None, status_code: int = 200, context: dict[str, Any] = {}, headers: dict[str, str] = {}):
    try:
        if page := resolve_page(path):
            markdown_ua = ["curl", "claude-user", "chatgpt-user", "google-extended", "perplexity-user"]
            markdown_mode = any([path.endswith(".md"), "text/markdown" in request.headers.get("accept", "").lower(), any([ua in request.headers.get("user-agent", "").lower() for ua in markdown_ua])])

            if page.endswith(".html"):
                if markdown_mode:
                    content = templates.env.get_template(page).render(request=request, **context)
                    soup = BeautifulSoup(content, "html.parser")
                    main = str(soup.find("main")) if soup.find("main") else content
                    content = markitdown.convert_stream(io.BytesIO(main.encode("utf-8")), file_extension=".html").text_content
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/markdown")
                else:
                    content = templates.env.get_template(page).render(request=request, **context)
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/html")

            elif page.endswith(".md"):
                with Directories.public.joinpath(page).open("r") as f:
                    markdown = f.read()

                if markdown_mode:
                    content = templates.env.from_string(markdown).render(request=request, **context)
                    response = PlainTextResponse(content, status_code=status_code, media_type="text/markdown")

                else:
                    if not markdown.startswith("---"):
                        front = {}
                        body = markdown
                    else:
                        end = markdown.find("\n---", 3)
                        if end == -1:
                            front = {}
                            body = markdown
                        else:
                            front = yaml.safe_load(markdown[3:end]) or {}
                            body = markdown[end+4:].lstrip("\n")

                    body_rendered = templates.env.from_string(body).render(request=request, **context)
                    html = htmlitdown(body_rendered)
                    source = f"{{% extends \"/base.html\" %}}\n"
                    for block in front:
                        source += f"{{% block {block} %}}{front[block]}{{% endblock %}}\n"
                    source += f"{{% block main %}}\n{html}\n{{% endblock %}}\n"

                    content = templates.env.from_string(source).render(request=request, **context)
                    response = Response(content=content, status_code=status_code, media_type="text/html")

            etag = '"' + hashlib.sha256(content.encode("utf-8")).hexdigest() + '"'
            if request.headers.get("if-none-match") == etag:
                response = Response(status_code=304, headers={"ETag": etag})
            else:
                response.headers["ETag"] = etag

            if access_counter:
                access_counter.increase()

        elif file := resolve_file(path):
            response = FileResponse(file, status_code=status_code)

        elif url := resolve_shorturl(path):
            response = RedirectResponse(url, status_code=status_code if 299 < status_code < 400 else 307)

        else:
            response = render_error_page(templates, request, 404, "リクエストしたページは現在ご利用になれません。削除/移動されたか、URLが間違っている可能性があります。", "そんなページ知らないっ！")

    except PermissionError:
        response = render_error_page(templates, request, 403, "何をしてるんです？脆弱性報告のためならいいのですが、データ盗んで悪用するためなら今すぐにやめてくださいね？", "ディレクトリトラバーサルね、知ってる。公開してないところ覗きたいの？えっt")

    for key, value in headers.items():
        response.headers[key.lower().strip()] = value

    return response

def render_error_page(request: Request, templates: Jinja2Templates, status_code: int, message: str | None = None, joke_message: str | None = None) -> Response:
    if Files.error.is_file():
        return render(
            str(Files.error.relative_to(Directories.public)),
            request=request,
            templates=templates,
            status_code=status_code,
            context={
                "status_code": status_code,
                "status_code_name": HTTPStatus(status_code).phrase,
                "message": message or ErrorMessages.normal.get(status_code, "不明なエラーが発生しました。"),
                "joke_message": joke_message or ErrorMessages.joke.get(status_code, "あんのーん")
            }
        )
    else:
        return PlainTextResponse(message or ErrorMessages.normal.get(status_code, "不明なエラーが発生しました。"), status_code=status_code)

thumbnail_font_dir = Directories.public.joinpath("assets", "fonts")
thumbnail_font_files = [
    str(thumbnail_font_dir / "MesloBIZUD-Regular.ttf"),
    str(thumbnail_font_dir / "InterBIZUD-Regular.ttf"),
    str(thumbnail_font_dir / "InterBIZUD-Bold.ttf")
]

def render_thumbnail_svg(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> str:
    if file := resolve_file(f"/assets/images/thumbnails/{template}.svg"):
        with file.open("r", encoding="utf-8") as f:
            svg = f.read()
        parts = [p for p in path.strip("/").split("/") if p]
        svg = svg.replace("__PATH__", escape("nercone.dev / " + " / ".join(parts) if parts else "nercone.dev"))
        svg = svg.replace("__TITLE__", escape(title))
        svg = svg.replace("__DESCRIPTION__", escape(description))
        return svg
    else:
        raise FileNotFoundError()

def render_thumbnail_png(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> bytes:
    svg = render_thumbnail_svg(path=path, title=title, description=description, template=template)
    png = resvg_py.svg_to_bytes(svg, font_files=thumbnail_font_files, width=1200, height=630)
    return png
