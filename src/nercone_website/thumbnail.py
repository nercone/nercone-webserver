import resvg_py
from html import escape
from .config import Directories
from .renderer import resolve_file, render_error_page

font_dir = Directories.public.joinpath("assets", "fonts")
font_files = [
    str(font_dir / "MesloBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Regular.ttf"),
    str(font_dir / "InterBIZUD-Bold.ttf")
]

def get_thumbnail_svg(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> str:
    if file := resolve_file("/assets/images/thumbnails/{name}.svg"):
        with file.open("r", encoding="utf-8") as f:
            svg = f.read()
        parts = [p for p in path.strip("/").split("/") if p]
        svg = svg.replace("__PATH__", escape("nercone.dev / " + " / ".join(parts) if parts else "nercone.dev"))
        svg = svg.replace("__TITLE__", escape(title))
        svg = svg.replace("__DESCRIPTION__", escape(description))
        return svg
    else:
        raise FileNotFoundError()

def get_thumbnail_png(path: str, title: str = "Untitled Page", description: str = "No description.", template: str = "normal") -> bytes:
    svg = get_thumbnail_svg(path=path, title=title, description=description, template=template)
    png = resvg_py.svg_to_bytes(svg, font_files=font_files, width=1200, height=630)
    return png
