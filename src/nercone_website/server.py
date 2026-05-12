import re
import httpx
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .config import Directories, Files, Repositories, Hostnames
from .renderer import render, render_error_page
from .thumbnail import get_thumbnail_png
from .database import AccessCounter
from .middleware import Middleware

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(Middleware)
templates = Jinja2Templates(directory=Directories.public)
access_counter = AccessCounter()

templates.env.globals["get_access_count"] = access_counter.get
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

@app.api_route("/ping", methods=["GET"])
async def ping(request: Request):
    return PlainTextResponse("pong!", status_code=200)

async def echo(request: Request):
    if not request.scope.get("trusted", False):
        return render_error_page(templates=templates, request=request, status_code=403, message="<code>/echo</code>エンドポイントはデバッグ用途のため、信頼されている一部のIP範囲からのアクセスに限定して許可されています。", joke_message="のっととらすてっど")
    return JSONResponse(request.scope["log"], status_code=200)

@app.api_route("/status", methods=["GET"])
async def status(request: Request):
    return JSONResponse(
        {
            "status": "ok",
            "version": {"server": Repositories.Server.version, "content": Repositories.Contents.version},
            "quote": get_daily_quote(),
            "counter": access_counter.get()
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

google_fonts_css_cache: dict = {"content": None, "expires_at": 0}
@app.api_route("/assets/css/google-fonts.css", methods=["GET"])
async def google_fonts_css(request: Request):
    now = datetime.now(timezone.utc).timestamp()
    if google_fonts_css_cache["content"] and now < google_fonts_css_cache["expires_at"]:
        return PlainTextResponse(google_fonts_css_cache["content"], status_code=200, media_type="text/css")

    async with httpx.AsyncClient() as client:
        css = await client.get("https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=BIZ+UDGothic&family=Noto+Sans+JP:wght@100..900&family=Noto+Sans+SC:wght@100..900&family=Noto+Sans+TC:wght@100..900&family=Noto+Sans+KR:wght@100..900&display=swap")

    if css.status_code == 200:
        google_fonts_css_cache["content"] = css.text
        google_fonts_css_cache["expires_at"] = now + 86400
        return PlainTextResponse(css.text, status_code=200, media_type="text/css")
    else:
        return render_error_page(templates=templates, request=request, status_code=502)

@app.api_route("/assets/images/thumbnails/{path:path}", methods=["GET"])
async def thumbnail(request: Request, path: str) -> Response:
    title = request.query_params.get("title", "Untitled Page")
    description = request.query_params.get("description", "No description.")
    template_type = request.query_params.get("template", "normal")

    png = get_thumbnail_png(path=path, title=title, description=description, template_type=template_type)
    return Response(content=png, media_type="image/png")

@app.api_route("/test/error-page/{status_code}", methods=["GET", "POST", "HEAD"])
async def fake_error_page(request: Request, status_code: int):
    return render_error_page(templates=templates, request=request, status_code=status_code)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD"])
async def default_response(request: Request, full_path: str) -> Response:
    return render(full_path, templates=templates, access_counter=access_counter, request=request)
