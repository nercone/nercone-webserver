import json
import uuid
import uvicorn
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
from nercone_modern.color import ModernColor
from nercone_modern.logging import ModernLogging
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from jinja2.exceptions import TemplateNotFound

app = FastAPI()
templates = Jinja2Templates(directory="templates")
log_filepath = Path(__file__).parent.joinpath("logs", f"{int(datetime.now(timezone.utc).timestamp())}.log")
logger = ModernLogging("nercone-webserver", filepath=log_filepath)

class AccessClientType(Enum):
    cURL = "cURL"
    Wget = "Wget"
    Firefox = "Firefox"
    Chrome = "Chrome"
    Opera = "Opera"
    Edge = "Edge"
    Safari = "Safari"
    Unknown = "Unknown"

@app.middleware("http")
async def middleware(request: Request, call_next):
    access_id = "access-" + str(uuid.uuid4()).lower()
    user_agent = request.headers.get("user-agent", "")
    request.state.client_type = AccessClientType.Unknown
    if "curl" in user_agent.lower():
        request.state.client_type = AccessClientType.cURL
    elif "wget" in user_agent.lower():
        request.state.client_type = AccessClientType.Wget
    elif "firefox" in user_agent.lower():
        request.state.client_type = AccessClientType.Firefox
    elif "opr" in user_agent.lower():
        request.state.client_type = AccessClientType.Opera
    elif "edg" in user_agent.lower():
        request.state.client_type = AccessClientType.Edge
    elif "chrome" in user_agent.lower():
        request.state.client_type = AccessClientType.Chrome
    elif "safari" in user_agent.lower():
        request.state.client_type = AccessClientType.Safari
    proxy_route = []
    origin_client_host = request.client.host
    if "X-Forwarded-For" in request.headers:
        proxy_route = request.headers.get("X-Forwarded-For").split(", ")
        origin_client_host = proxy_route[0]
    exception: Exception | None = None
    try:
        response = await call_next(request)
    except Exception as e:
        exception = e
        response = PlainTextResponse("Internal Server Error", status_code=500)
    response.headers["Server"] = "Nercone Web Server"
    access_log_dir = Path(__file__).parent.joinpath("logs", "access")
    if not access_log_dir.exists():
        access_log_dir.mkdir(parents=True, exist_ok=True)
    with access_log_dir.joinpath(f"{access_id}.txt").open("w") as f:
        f.write(f"----- RESPONSE -----\n")
        f.write(f"CODE: {response.status_code}\n")
        f.write(f"CHAR: {response.charset}\n")
        f.write(f"MEDT: {response.media_type}\n")
        f.write(f"----- REQUEST -----\n")
        f.write(f"HOST: {request.client.host}\n")
        f.write(f"PORT: {request.client.port}\n")
        f.write(f"ORGN: {origin_client_host}\n")
        f.write(f"TYPE: {request.state.client_type}\n")
        f.write(f"URL : {request.url}\n")
        f.write(f"----- ROUTE -----\n")
        for i in range(len(proxy_route)):
            if i == 0:
                f.write(f"{proxy_route[i]} (ORIGIN)\n")
            elif i == len(proxy_route) - 1:
                f.write(f"{proxy_route[i]} (LAST)\n")
            else:
                f.write(f"{proxy_route[i]}\n")
        f.write(f"----- HEADER -----\n")
        for key, value in request.headers.items():
            f.write(f"{key}: {value}\n")
        f.write(f"----- COOKIE -----\n")
        for key, value in request.cookies.items():
            f.write(f"{key}: {value}\n")
        if exception:
            f.write(f"----- EXCEPTION -----\n")
            f.write(str(exception))
            f.write("\n")
    status_code_color = "blue"
    if response.status_code == 200 or response.status_code == 307:
        status_code_color = "green"
    elif response.status_code == 400:
        status_code_color = "yellow"
    elif response.status_code == 403:
        status_code_color = "yellow"
    elif response.status_code == 404:
        status_code_color = "yellow"
    elif response.status_code == 500:
        status_code_color = "red"
    logger.log(f"{ModernColor.color(status_code_color)}{response.status_code}{ModernColor.color('reset')} {access_id} FROM {request.client.host} ORGN {origin_client_host} USING {request.state.client_type}")
    return response

@app.get("/to/{url_id}")
async def short_url(request: Request, url_id: str):
    json_path = Path(__file__).parent / "shorturls.json"
    if not json_path.exists():
        return PlainTextResponse("Short URL configuration file not found.", status_code=500)
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return PlainTextResponse("Failed to load Short URL configuration.", status_code=500)
    current_id = url_id
    visited = set()
    for _ in range(10):
        if current_id in visited:
            return PlainTextResponse("Circular alias detected.", status_code=500)
        visited.add(current_id)
        if current_id not in data:
            break
        entry = data[current_id]
        entry_type = entry.get("type")
        content = entry.get("content")
        if entry_type == "redirect":
            return RedirectResponse(url=content)
        elif entry_type == "alias":
            current_id = content
        else:
            break
    return templates.TemplateResponse(
        status_code=404,
        request=request,
        name="404.html"
    )

@app.get("/{full_path:path}")
async def default_response(request: Request, full_path: str) -> Response:
    if full_path == "" or full_path == "/":
        template_name = "index.html"
    elif not full_path.endswith(".html"):
        base_dir = Path(__file__).parent / "files"
        target_path = (base_dir / full_path).resolve()
        if not str(target_path).startswith(str(base_dir.resolve())):
            return PlainTextResponse("Blocked by Nercone Web Server", status_code=403)
        if target_path.exists() and target_path.is_file():
            return FileResponse(target_path)
        else:
            return templates.TemplateResponse(
                status_code=404,
                request=request,
                name="404.html"
            )
    else:
        template_name = full_path
    try:
        return templates.TemplateResponse(
            status_code=200,
            request=request,
            name=template_name
        )
    except TemplateNotFound:
        return templates.TemplateResponse(
            status_code=404,
            request=request,
            name="404.html"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="error")
