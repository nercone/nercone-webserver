import resvg_py
from html import escape
from .config import Directories

font_dir = Directories.public.joinpath("assets", "fonts")
font_files = [
    str(font_dir / "MesloBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Bold.ttf")
]
template_cache: dict = {}

def get_thumbnail_template(template_type: str) -> str:
    if template_type not in template_cache:
        svg_file = Directories.public.joinpath("assets", "images", "thumbnails", "error.svg" if template_type == "error" else "normal.svg")
        with svg_file.open("r", encoding="utf-8") as f:
            template_cache[template_type] = f.read()
    return template_cache[template_type]

def get_thumbnail_svg(path: str, title: str = "Untitled Page", description: str = "No description.", template_type: str = "normal") -> str:
    parts = [p for p in path.strip("/").split("/") if p]
    path_display = "nercone.dev / " + " / ".join(parts) if parts else "nercone.dev"

    svg = get_thumbnail_template(template_type)
    svg = svg.replace("__PATH__", escape(path_display))
    svg = svg.replace("__TITLE__", escape(title))
    svg = svg.replace("__DESCRIPTION__", escape(description))
    return svg

def get_thumbnail_png(path: str, title: str = "Untitled Page", description: str = "No description.", template_type: str = "normal") -> bytes:
    svg = get_thumbnail_svg(path=path, title=title, description=description, template_type=template_type)
    png = resvg_py.svg_to_bytes(svg, font_files=font_files, width=1200, height=630)
    return png
