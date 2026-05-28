import json
from pathlib import Path

from .manager import TimingManager
from .constants import Directories

def resolve_file(path: str) -> Path | None:
    full_path = Directories.public.joinpath(path.lstrip("/")).resolve()
    if not full_path.is_relative_to(Directories.public):
        raise PermissionError()
    return full_path if full_path.is_file() else None

def resolve_page(path: str, markdown_mode: bool = False, timings: TimingManager | None = None) -> str | None:
    if timings:
        timings.start("resolve-page")

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

    if markdown_mode:
        candidates = markdown_candidates + template_candidates 
    else:
        candidates = template_candidates + markdown_candidates

    for candidate in candidates:
        if file := resolve_file(candidate):
            timings.stop("resolve-page")
            return str(file.relative_to(Directories.public))

    if timings:
        timings.stop("resolve-page")

    return None

def resolve_shorturl(path: str, timings: TimingManager | None = None) -> str | None:
    if timings:
        timings.start("resolve-shorturl")

    max_retry = 10

    if file := resolve_file("shorturls.json"):
        with file.open("r", encoding="utf-8") as f:
            shorturls = json.load(f)

        current = path.strip("/")
        visited = set()

        for _ in range(max_retry):
            if current in visited or current not in shorturls:
                timings.stop("resolve-shorturl")
                return None

            visited.add(current)

            entry = shorturls[current]
            if entry["type"] == "redirect":
                timings.stop("resolve-shorturl")
                return entry["content"]
            elif entry["type"] == "alias":
                current = entry["content"]

    if timings:
        timings.stop("resolve-shorturl")

    return None
