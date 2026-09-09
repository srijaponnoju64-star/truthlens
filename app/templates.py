"""Shared Jinja2Templates instance — import from here in all routes."""
from pathlib import Path
from fastapi.templating import Jinja2Templates

# Resolve templates dir relative to this file so it works no matter
# which working directory uvicorn is started from.
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
