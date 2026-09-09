import re
import requests
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.services.text_service import analyze_text
from app.database.db import save_detection
from app.templates import templates

router = APIRouter()


def _fetch_url(url):
    # type: (str) -> Optional[str]
    try:
        r = requests.get(url, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        html = r.text
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:3000]
    except Exception as e:
        print("URL fetch error:", e)
        return None


@router.get("/text", response_class=HTMLResponse)
async def text_page(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "module": "text"}
    )


@router.post("/text/analyze", response_class=HTMLResponse)
async def analyze_text_route(
    request: Request,
    text: Optional[str] = Form(None),
    text_url: Optional[str] = Form(None),
):
    try:
        final_text = None
        source_url = None

        if text_url and text_url.strip():
            source_url = text_url.strip()
            fetched = _fetch_url(source_url)
            final_text = (
                f"URL: {source_url}\n\nContent: {fetched}"
                if fetched else f"URL provided: {source_url}"
            )
        elif text and text.strip():
            final_text = text.strip()

        if not final_text:
            return _render_error(request, "No text provided. Please enter text or a URL.")

        result = analyze_text(final_text, source_url=source_url)
        save_detection(
            module="TEXT",
            input_text=final_text[:500],
            image_path=None, audio_path=None,
            verdict=result["verdict"], confidence=result["confidence"],
            source=result["source"], spread_by=result["spread_by"],
            explanation=result["explanation"],
        )

        return templates.TemplateResponse(
            "result.html",
            {"request": request, "result": result,
             "module": "Text Analysis",
             "input_text": final_text[:300], "image_path": None},
        )

    except Exception as e:
        print("text_route error:", e)
        return _render_error(request, str(e))


def _render_error(request: Request, msg: str):
    return templates.TemplateResponse(
        "result.html",
        {"request": request,
         "result": {"verdict": "ERROR", "confidence": "N/A",
                    "source": "N/A", "spread_by": "N/A",
                    "explanation": msg},
         "module": "Text Analysis",
         "input_text": None, "image_path": None},
    )
