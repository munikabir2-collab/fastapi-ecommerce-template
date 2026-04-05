# templates.py

from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

templates = Jinja2Templates(directory="templates")

templates.env = Environment(
    loader=FileSystemLoader("templates"),
    auto_reload=True,
    cache_size=0
)