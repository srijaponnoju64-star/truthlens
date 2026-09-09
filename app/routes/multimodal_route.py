import os
import shutil
import base64
import requests
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse

from app.services.fusion_service import analyze_multimodal
from app.database.db import save_detection
from app.templates import templates

router = APIRouter()
UPLOAD_DIR = str(Path(__file__).parent.parent.parent / "uploads")


# ── helpers ────────────────────────────────────────────────────────────────────

def _save_upload(upload: UploadFile, name: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return path


def _resolve_image(image, image_url, pasted_image, fallback_name):
    if image and image.filename:
        return _save_upload(image, image.filename)
    if image_url and image_url.strip():
        r = requests.get(image_url.strip(), timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        path = os.path.join(UPLOAD_DIR, fallback_name)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    if pasted_image and pasted_image.strip():
        raw = (pasted_image.split("base64,")[1]
               if "base64," in pasted_image else pasted_image)
        path = os.path.join(UPLOAD_DIR, "pasted_post_image.png")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(raw))
        return path
    return None


def _render_error(request: Request, msg: str, module_label: str, text: str = None):
    return templates.TemplateResponse(
        "result.html",
        {"request": request,
         "result": {"verdict": "ERROR", "confidence": "N/A",
                    "source": "N/A", "spread_by": "N/A",
                    "explanation": msg},
         "module": module_label,
         "input_text": text, "image_path": None},
    )


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("/multimodal", response_class=HTMLResponse)
async def multimodal_page(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "module": "multimodal"}
    )


@router.post("/multimodal/analyze", response_class=HTMLResponse)
async def analyze_multimodal_route(
    request: Request,
    module_type: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    pasted_image: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
):
    try:
        image_path = _resolve_image(image, image_url, pasted_image, "url_post_image.jpg")
        audio_path = _save_upload(audio, audio.filename) if audio and audio.filename else None

        result = analyze_multimodal(text=text, image_path=image_path, audio_path=audio_path)

        save_detection(
            module="MULTIMODAL",
            input_text=text, image_path=image_path, audio_path=audio_path,
            verdict=result["verdict"], confidence=result["confidence"],
            source=result["source"], spread_by=result["spread_by"],
            explanation=result["explanation"],
        )
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "result": result,
             "module": "Multimodal Analysis", "input_text": text,
             "image_path": "/uploads/" + os.path.basename(image_path) if image_path else None},
        )

    except Exception as e:
        print("multimodal_route error:", e)
        return _render_error(request, str(e), "Multimodal Analysis", text)


@router.post("/multimodal/analyze_video", response_class=HTMLResponse)
async def analyze_video_route(
    request: Request,
    video: Optional[UploadFile] = File(None),
):
    image_path = None
    audio_path = None
    try:
        if video and video.filename:
            video_path = _save_upload(video, video.filename)
            image_path, audio_path = _extract_from_video(video_path)

        result = analyze_multimodal(text=None, image_path=image_path, audio_path=audio_path)

        save_detection(
            module="VIDEO",
            input_text=None, image_path=image_path, audio_path=audio_path,
            verdict=result["verdict"], confidence=result["confidence"],
            source=result["source"], spread_by=result["spread_by"],
            explanation=result["explanation"],
        )
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "result": result,
             "module": "Video Analysis",
             "input_text": f"Video: {video.filename if video else 'uploaded'}",
             "image_path": "/uploads/" + os.path.basename(image_path) if image_path else None},
        )

    except Exception as e:
        print("video_route error:", e)
        return _render_error(request, str(e), "Video Analysis")


def _extract_from_video(video_path):
    frame_path = None
    audio_path = None
    try:
        from moviepy.editor import VideoFileClip
        from PIL import Image
        import numpy as np

        clip = VideoFileClip(video_path)
        frame = clip.get_frame(min(1, clip.duration - 0.1))
        frame_path = os.path.splitext(video_path)[0] + "_frame.jpg"
        Image.fromarray(frame.astype("uint8")).save(frame_path)

        if clip.audio:
            audio_path = os.path.splitext(video_path)[0] + "_audio.wav"
            clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        clip.close()
    except Exception as e:
        print("_extract_from_video error:", e)
    return frame_path, audio_path
