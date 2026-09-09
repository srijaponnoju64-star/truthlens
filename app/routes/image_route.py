import os
import shutil
import base64
import requests
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse

from app.services.image_service import analyze_image
from app.database.db import save_detection
from app.templates import templates

router = APIRouter()
UPLOAD_DIR = str(Path(__file__).parent.parent.parent / "uploads")


@router.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "module": "image"}
    )


@router.post("/image/analyze", response_class=HTMLResponse)
async def analyze_image_route(
    request: Request,
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    pasted_image: Optional[str] = Form(None),
):
    file_path = None
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        if image and image.filename:
            file_path = os.path.join(UPLOAD_DIR, image.filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(image.file, f)

        elif image_url and image_url.strip():
            r = requests.get(image_url.strip(), timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
            file_path = os.path.join(UPLOAD_DIR, "url_image.jpg")
            with open(file_path, "wb") as f:
                f.write(r.content)

        elif pasted_image and pasted_image.strip():
            raw = (pasted_image.split("base64,")[1]
                   if "base64," in pasted_image else pasted_image)
            file_path = os.path.join(UPLOAD_DIR, "pasted_image.png")
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(raw))

        if not file_path:
            return _render_error(request,
                                 "No image provided. Please upload, paste or enter a URL.")

        result = analyze_image(file_path)
        save_detection(
            module="IMAGE",
            input_text=image_url or None,
            image_path=file_path, audio_path=None,
            verdict=result["verdict"], confidence=result["confidence"],
            source=result["source"], spread_by=result["spread_by"],
            explanation=result["explanation"],
        )
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "result": result,
             "module": "Image Analysis",
             "input_text": None,
             "image_path": "/uploads/" + os.path.basename(file_path)},
        )

    except Exception as e:
        print("image_route error:", e)
        return _render_error(request, str(e))


def _render_error(request: Request, msg: str):
    return templates.TemplateResponse(
        "result.html",
        {"request": request,
         "result": {"verdict": "ERROR", "confidence": "N/A",
                    "source": "N/A", "spread_by": "N/A",
                    "explanation": msg},
         "module": "Image Analysis",
         "input_text": None, "image_path": None},
    )