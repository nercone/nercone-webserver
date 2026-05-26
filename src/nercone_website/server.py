from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse

from .config import Repositories
from .renderer import default_response, render_error_page, render_thumbnail_png
from .middleware import Middleware
from .templates import get_daily_quote, access_counter

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(Middleware)

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

@app.api_route("/assets/images/thumbnail/template/{template}", methods=["GET"])
async def thumbnail(request: Request, template: str) -> Response:
    path = request.query_params.get("path", "/")
    title = request.query_params.get("title", "Untitled Page")
    description = request.query_params.get("description", "No description.")

    try:
        png = render_thumbnail_png(path=path, title=title, description=description, template=template)
        return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-cache"})
    except FileNotFoundError:
        return render_error_page(request=request, status_code=500, message="サムネイルの生成に必要なテンプレートが見つかりません。", joke_message="はにゃ？")
    except PermissionError:
        return render_error_page(request=request, status_code=403, message="ねえ、今サムネイル生成のエンドポイント悪用して攻撃しようとした？したよね？？ディレクトリトラバーサルでしょ？知ってるよ？怒ってないから正直に言って？ね？ね？？", joke_message="嘘つきには針千本プレゼント！このメッセージを読んだ後、100年以内限定！飲用補助サービスが無料でついてきます！今すぐ正直に言え！！")

@app.api_route("/error/{status_code}", methods=["GET"])
async def fake_error_page(request: Request, status_code: str):
    if status_code.isnumeric():
        return render_error_page(request=request, status_code=int(status_code))
    elif status_code == "server":
        return render_error_page(request=request, status_code=500)
    elif status_code == "nginx":
        return render_error_page(request=request, status_code=502)
    else:
        return render_error_page(request=request, status_code=400, message="errorエンドポイントのパスには「server」「nginx」またはHTTPレスポンスステータスコードのみが使用可能です。", joke_message="HTTP/1.1 600 Not Normal")

@app.api_route("/{path:path}", methods=["GET", "POST", "HEAD"])
async def default_route(request: Request, path: str) -> Response:
    return default_response(path, request=request)
