import io
import re
import json
import yaml
import random
import mistune
import resvg_py
import requests
from html import escape
from pathlib import Path
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse, RedirectResponse
from .error import error_page
from .config import Directories, Files, Repositories, Hostnames
from .database import AccessCounter
from .middleware import Middleware

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(Middleware)
templates = Jinja2Templates(directory=Directories.public)
markitdown = MarkItDown()
accesscounter = AccessCounter()

class CustomHTMLRenderer(mistune.HTMLRenderer):
    def block_code(self, code, **attrs):
        return f'<pre>{mistune.escape(code)}</pre>\n'
htmlitdown = mistune.create_markdown(renderer=CustomHTMLRenderer(escape=False), plugins=["table"])

templates.env.globals["get_access_count"] = accesscounter.get
templates.env.globals["server_version"] = Repositories.Server.version
templates.env.globals["contents_version"] = Repositories.Contents.version
templates.env.globals["onion_site_url"] = f"http://{Hostnames.onion}/"
templates.env.filters["re_sub"] = lambda s, pattern, repl: re.sub(pattern, repl, s)

def this_year() -> int:
    return datetime.now(ZoneInfo("Asia/Tokyo")).year
templates.env.globals["this_year"] = this_year

def this_year_in_heisei() -> int: # heysay is not ended.
    return datetime.now(ZoneInfo("Asia/Tokyo")).year - 1988
templates.env.globals["this_year_in_heisei"] = this_year_in_heisei

def get_daily_quote() -> str:
    if Files.quotes.is_file():
        seed = str(datetime.now(timezone.utc).date())
        with Files.quotes.open("r") as f:
            quotes = f.read().strip().split("\n")
        return random.Random(seed).choice(quotes)
    else:
        return "GReeeeN KA-RA-DA"
templates.env.globals["get_daily_quote"] = get_daily_quote

def resolve_file(full_path: str) -> Path | None:
    path = Directories.public.joinpath(full_path).resolve()
    if not path.is_relative_to(Directories.public):
        raise PermissionError()
    return path if path.is_file() else None

def resolve_page(full_path: str) -> str | None:
    if full_path in ["", "/"]:
        template_candidates = ["index.html", "README.html"]
        markdown_candidates = ["index.md",   "README.md"]
    elif full_path.endswith(".html"):
        template_candidates = [f"{full_path[:-5].strip('/')}.html"]
        markdown_candidates = [f"{full_path[:-5].strip('/')}.md"]
    elif full_path.endswith(".md"):
        template_candidates = [f"{full_path[:-3].strip('/')}.html"]
        markdown_candidates = [f"{full_path[:-3].strip('/')}.md"]
    else:
        template_candidates = [f"{full_path.strip('/')}.html", f"{full_path.strip('/')}/index.html", f"{full_path.strip('/')}/README.html"]
        markdown_candidates = [f"{full_path.strip('/')}.md",   f"{full_path.strip('/')}/index.md",   f"{full_path.strip('/')}/README.md"]

    candidates = template_candidates + markdown_candidates
    for candidate in candidates:
        if file := resolve_file(candidate):
            return str(file.relative_to(Directories.public))

    return None

def resolve_shorturl(full_path: str) -> str | None:
    max_retry = 10

    if Files.shorturls.is_file():
        shorturls = json.load(Files.shorturls.open("r", encoding="utf-8"))

        current = full_path.strip("/")
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

@app.api_route("/ping", methods=["GET"])
async def ping(request: Request):
    return PlainTextResponse("pong!", status_code=200)

@app.api_route("/echo", methods=["GET"])
async def echo(request: Request):
    return JSONResponse(request.scope["log"], status_code=200)

@app.api_route("/status", methods=["GET"])
async def status(request: Request):
    return JSONResponse(
        {
            "status": "ok",
            "version": {"server": Repositories.Server.version, "content": Repositories.Contents.version},
            "daily_quote": get_daily_quote(),
            "access_count": accesscounter.get()
        },
        status_code=200
    )

@app.api_route("/welcome", methods=["GET"])
async def welcome(request: Request):
    return PlainTextResponse(
        f"""
■   ■ ■■■■■ ■■■■   ■■■■  ■■■  ■   ■ ■■■■■
■■  ■ ■     ■   ■ ■     ■   ■ ■■  ■ ■
■■  ■ ■     ■   ■ ■     ■   ■ ■■  ■ ■
■ ■ ■ ■■■■  ■■■■  ■     ■   ■ ■ ■ ■ ■■■■
■  ■■ ■     ■ ■   ■     ■   ■ ■  ■■ ■
■  ■■ ■     ■  ■  ■     ■   ■ ■  ■■ ■
■   ■ ■■■■■ ■   ■  ■■■■  ■■■  ■   ■ ■■■■■

nercone.dev ({Repositories.Server.version}+{Repositories.Contents.version})
welcome to nercone.dev!
        """.strip() + "\n",
        status_code=200
    )

@app.api_route("/error/{code}", methods=["GET", "POST", "HEAD"])
async def fake_error_page(request: Request, code: str):
    return error_page(templates=templates, request=request, status_code=int(code))

google_fonts_css_cache: dict = {"content": None, "expires_at": 0}
@app.api_route("/assets/css/google-fonts.css", methods=["GET"])
async def google_fonts_css(request: Request):
    now = datetime.now(timezone.utc).timestamp()
    if google_fonts_css_cache["content"] and now < google_fonts_css_cache["expires_at"]:
        return PlainTextResponse(google_fonts_css_cache["content"], status_code=200, media_type="text/css")

    css = requests.get("https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=BIZ+UDGothic&family=Noto+Sans+JP:wght@100..900&family=Noto+Sans+SC:wght@100..900&family=Noto+Sans+TC:wght@100..900&family=Noto+Sans+KR:wght@100..900&display=swap")
    if css.status_code == 200:
        google_fonts_css_cache["content"] = css.text
        google_fonts_css_cache["expires_at"] = now + 86400

    return PlainTextResponse(css.text or "Failed to retrieve the Google Fonts CSS file.", status_code=200 if css.status_code == 200 else 500, media_type="text/css")

@app.api_route("/assets/images/thumbnails/{path:path}", methods=["GET"])
async def thumbnail(request: Request, path: str) -> Response:
    title = request.query_params.get("title", "Untitled Page")
    description = request.query_params.get("description", "No description.")
    template_type = request.query_params.get("template", "normal")

    parts = [p for p in path.strip("/").split("/") if p]
    path_display = "nercone.dev / " + " / ".join(parts) if parts else "nercone.dev"

    font_dir = Directories.public.joinpath("assets", "fonts")
    font_files = [
        str(font_dir / "MesloBIZUD-Regular.ttf"),
        str(font_dir / "InterBIZUD-Regular.ttf"),
        str(font_dir / "InterBIZUD-Bold.ttf")
    ]

    svg_file = Directories.public.joinpath("assets", "images", "thumbnails", "error.svg" if template_type == "error" else "normal.svg")

    svg = svg_file.read_text(encoding="utf-8")
    svg = svg.replace("__PATH__", escape(path_display))
    svg = svg.replace("__TITLE__", escape(title))
    svg = svg.replace("__DESCRIPTION__", escape(description))

    png = resvg_py.svg_to_bytes(svg, font_files=font_files, width=1200, height=630)
    return Response(content=png, media_type="image/png")

@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD"])
async def default_response(request: Request, full_path: str) -> Response:
    try:
        if page := resolve_page(full_path):
            markdown_ua = ["curl", "claude-user", "chatgpt-user", "google-extended", "perplexity-user"]
            markdown_mode = any([full_path.endswith(".md"), "text/markdown" in request.headers.get("accept", "").lower(), any([ua in request.headers.get("user-agent", "").lower() for ua in markdown_ua])])

            if page.endswith(".html"):
                if markdown_mode:
                    content = templates.env.get_template(page).render(request=request)
                    soup = BeautifulSoup(content, "html.parser")
                    main = str(soup.find("main")) if soup.find("main") else content
                    markdown = markitdown.convert_stream(io.BytesIO(main.encode("utf-8")), file_extension=".html")
                    response = PlainTextResponse(markdown.text_content, status_code=200, media_type="text/markdown")
                else:
                    content = templates.env.get_template(page).render(request=request)
                    response = PlainTextResponse(content, status_code=200, media_type="text/html")

            elif page.endswith(".md"):
                with Directories.public.joinpath(page).open("r") as f:
                    markdown = f.read()

                if markdown_mode:
                    content = templates.env.from_string(markdown).render(request=request)
                    response = PlainTextResponse(content, status_code=200, media_type="text/markdown")

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

                    body_rendered = templates.env.from_string(body).render(request=request)
                    html = htmlitdown(body_rendered)
                    source = f"{{% extends \"/base.html\" %}}\n"
                    for block in front:
                        source += f"{{% block {block} %}}{front[block]}{{% endblock %}}\n"
                    source += f"{{% block main %}}\n{html}\n{{% endblock %}}\n"

                    content = templates.env.from_string(source).render(request=request)
                    response = Response(content=content, status_code=200, media_type="text/html")

            accesscounter.increase()
            return response

        else:
            if file := resolve_file(full_path):
                return FileResponse(file)

    except PermissionError:
        return error_page(templates, request, 403, "何をしてるんです？脆弱性報告のためならいいのですが、データ盗んで悪用するためなら今すぐにやめてくださいね？", "ディレクトリトラバーサルね、知ってる。公開してないところ覗きたいの？えっt")

    if result := resolve_shorturl(full_path):
        return RedirectResponse(url=result)

    return error_page(templates, request, 404, "リクエストしたページは現在ご利用になれません。削除/移動されたか、URLが間違っている可能性があります。", "そんなページ知らないっ！")
