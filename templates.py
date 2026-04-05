# templates.py

from fastapi.templating import Jinja2Templates

# Single shared templates instance (पूरे project में यही use होगा)
templates = Jinja2Templates(directory="templates")