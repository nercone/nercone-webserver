import resvg_py
from html import escape
from .config import Directories
from .renderer import resolve_file

font_dir = Directories.public.joinpath("assets", "fonts")
font_files = [
    str(font_dir / "MesloBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Bold.ttf")
]
template_cache: dict = {}

def get_thumbnail_template(name: str) -> str:
    if name not in template_cache:
        if file := resolve_file("/assets/images/thumbnails/{name}.svg"):
            with file.open("r", encoding="utf-8") as f:
                template_cache[name] = f.read()
    return template_cache[name]

def get_thumbnail_svg(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> str:
    parts = [p for p in path.strip("/").split("/") if p]
    svg = get_thumbnail_template(template)
    svg = svg.replace("__PATH__", escape("nercone.dev / " + " / ".join(parts) if parts else "nercone.dev"))
    svg = svg.replace("__TITLE__", escape(title))
    svg = svg.replace("__DESCRIPTION__", escape(description))
    return svg

def get_thumbnail_png(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> bytes:
    svg = get_thumbnail_svg(path=path, title=title, description=description, template=template)
    png = resvg_py.svg_to_bytes(svg, font_files=font_files, width=1200, height=630)
    return png
