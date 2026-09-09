import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routes import text_route, image_route, multimodal_route
from app.database.db import init_db, get_all_detections

app = FastAPI(title="TruthLens - Multimodal Fake Detector")

app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

init_db()

app.include_router(text_route.router)
app.include_router(image_route.router)
app.include_router(multimodal_route.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "module": "home"})

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    rows = get_all_detections()
    detections = [list(row) for row in rows]
    return templates.TemplateResponse("history.html", {"request": request, "detections": detections})
