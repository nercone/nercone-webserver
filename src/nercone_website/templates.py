import re
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi.templating import Jinja2Templates

from .resolver import resolve_file
from .constants import Directories, Repositories, Hostnames
from .databases import AccessCounter

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
    if file := resolve_file("quotes.txt"):
        seed = str(datetime.now(timezone.utc).date())
        with file.open("r") as f:
            quotes = f.read().strip().split("\n")
        return random.Random(seed).choice(quotes)
    else:
        return "GReeeeN KA-RA-DA"
templates.env.globals["get_daily_quote"] = get_daily_quote
