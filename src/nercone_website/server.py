import re
import json
import httpx
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .config import Directories, Files, Repositories, Hostnames
from .renderer import render, render_error_page, render_thumbnail_png
from .database import AccessCounter
from .middleware import Middleware

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(Middleware)

access_counter = AccessCounter()

templates = Jinja2Templates(directory=Directories.public)
templates.env.filters["re_sub"] = lambda s, pattern, repl: re.sub(pattern, repl, s)
templates.env.globals["access_counter"] = access_counter
templates.env.globals["Repositories"] = Repositories
templates.env.globals["Hostnames"] = Hostnames

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
async def ping():
    return PlainTextResponse("pong!", status_code=200)

@app.api_route("/welcome", methods=["GET"])
async def welcome():
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

@app.api_route("/status", methods=["GET"])
async def status():
    return JSONResponse(
        {
            "status": "ok",
            "version": {"server": Repositories.Server.version, "content": Repositories.Contents.version},
            "quote": get_daily_quote(),
            "counter": access_counter.get()
        },
        status_code=200
    )

@app.api_route("/assets/css/google-fonts.css", methods=["GET"])
async def google_fonts_css(request: Request):
    now = datetime.now(timezone.utc).timestamp()
    if Files.Cache.google_fonts.is_file():
        try:
            cached = json.loads(Files.Cache.google_fonts.read_text(encoding="utf-8"))
            if cached.get("expires_at", 0) > now:
                return PlainTextResponse(cached["content"], status_code=200, media_type="text/css")
        except Exception:
            pass

    async with httpx.AsyncClient() as client:
        css = await client.get("https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@100..900&family=Noto+Sans+SC:wght@100..900&family=Noto+Sans+TC:wght@100..900&family=Noto+Sans+KR:wght@100..900&display=swap")

    if css.status_code == 200:
        Files.Cache.google_fonts.write_text(json.dumps({"content": css.text, "expires_at": now + 86400}, ensure_ascii=False), encoding="utf-8")
        return PlainTextResponse(css.text, status_code=200, media_type="text/css")
    else:
        return render_error_page(request=request, templates=templates, status_code=502)

@app.api_route("/assets/images/thumbnail/template/{template}", methods=["GET"])
async def thumbnail(request: Request, template: str) -> Response:
    path = request.query_params.get("path", "/")
    title = request.query_params.get("title", "Untitled Page")
    description = request.query_params.get("description", "No description.")

    try:
        png = render_thumbnail_png(path=path, title=title, description=description, template=template)
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-cache"})
    except FileNotFoundError:
        return render_error_page(request=request, templates=templates, status_code=500, message="サムネイルの生成に必要なテンプレートが見つかりません。", joke_message="はにゃ？")
    except PermissionError:
        return render_error_page(request=request, templates=templates, status_code=403, message="ねえ、今サムネイル生成のエンドポイント悪用して攻撃しようとした？したよね？？ディレクトリトラバーサルでしょ？知ってるよ？怒ってないから正直に言って？ね？ね？？", joke_message="嘘つきには針千本プレゼント！このメッセージを読んだ後、100年以内限定！飲用補助サービスが無料でついてきます！今すぐ正直に言え！！")

@app.api_route("/error/{status_code}", methods=["GET"])
async def fake_error_page(request: Request, status_code: str):
    if status_code.isnumeric():
        return render_error_page(request=request, templates=templates, status_code=int(status_code))
    elif status_code == "nginx":
        return render_error_page(request=request, templates=templates, status_code=502)
    else:
        return render_error_page(request=request, templates=templates, status_code=400, message="errorエンドポイントのパスには「nginx」またはHTTPレスポンスステータスコードのみが使用可能です。", joke_message="HTTP/1.1 600 Not Normal")

@app.api_route("/{path:path}", methods=["GET", "POST", "HEAD"])
async def default_response(request: Request, path: str) -> Response:
    return render(path, request=request, templates=templates, access_counter=access_counter)
