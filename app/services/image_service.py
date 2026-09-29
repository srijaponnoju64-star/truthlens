import os
import re
import base64
import io
from app.config import groq_client

MODEL_NAME = "qwen/qwen3.8-27b"

_PROMPT = """You are a world-class expert at detecting fake, manipulated or AI-generated images.
Look carefully at the attached image. Check for signs of manipulation, deepfake, AI-generation, or false context.
Respond in EXACTLY this format (no extra lines):
VERDICT: FAKE
CONFIDENCE: 88%
SOURCE: Facebook, Instagram, WhatsApp forwards
SPREAD_BY: Anonymous accounts, political groups
EXPLANATION: This image shows signs of digital manipulation in lighting and shadows.
Rules:
- VERDICT must be exactly FAKE or REAL
- SOURCE must name specific platforms
- If REAL -> SOURCE = Verified news agencies Reuters AP PTI and SPREAD_BY = Verified photojournalists
- NEVER put N/A for SOURCE when FAKE
"""


def _resize_image(image_bytes: bytes, max_size_kb: int = 800) -> tuple:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        quality = 85
        while True:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            if len(buf.getvalue()) <= max_size_kb * 1024 or quality < 20:
                break
            img = img.resize((int(img.width * 0.75), int(img.height * 0.75)))
            quality -= 10
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


def analyze_image(image_path: str) -> dict:
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_bytes, mime = _resize_image(image_bytes)
        image_data = base64.b64encode(image_bytes).decode()
        return _call_api(image_data, mime)
    except Exception as e:
        print("image_service error:", e)
        return _error(str(e))


def analyze_image_from_base64(image_data: str, mime_type: str = "image/jpeg") -> dict:
    try:
        image_bytes = base64.b64decode(image_data)
        image_bytes, mime = _resize_image(image_bytes)
        image_data = base64.b64encode(image_bytes).decode()
        return _call_api(image_data, mime)
    except Exception as e:
        print("image_service (b64) error:", e)
        return _error(str(e))


def _call_api(image_data: str, mime: str) -> dict:
    # The image is now really sent to the model (before, only the text was sent)
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": _PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{image_data}"}},
            ],
        }],
        temperature=0.2,
        max_tokens=600,
    )
    return _parse(response.choices[0].message.content)


def _parse(raw: str) -> dict:
    data = {"verdict": "UNKNOWN", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A", "explanation": "N/A"}
    for line in raw.strip().splitlines():
        line = line.strip().strip("*").strip()
        if line.startswith("VERDICT:"):
            data["verdict"] = re.sub(r"[^A-Z]", "", line[8:].upper()) or "UNKNOWN"
        elif line.startswith("CONFIDENCE:"):
            data["confidence"] = line[11:].strip()
        elif line.startswith("SOURCE:"):
            data["source"] = line[7:].strip()
        elif line.startswith("SPREAD_BY:"):
            data["spread_by"] = line[10:].strip()
        elif line.startswith("EXPLANATION:"):
            data["explanation"] = line[12:].strip()
    return data


def _error(msg: str) -> dict:
    return {"verdict": "ERROR", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": msg[:300]}