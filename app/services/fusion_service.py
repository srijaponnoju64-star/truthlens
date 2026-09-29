import os
import re
import base64
import io
from app.config import groq_client
from app.services.audio_service import transcribe_audio

MODEL_NAME = "qwen/qwen3.8-27b"


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


def _load_image_as_data_url(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_bytes, mime = _resize_image(image_bytes)
    b64 = base64.b64encode(image_bytes).decode()
    return f"data:{mime};base64,{b64}"


def analyze_multimodal(text=None, image_path=None, audio_path=None):
    try:
        transcription = ""
        if audio_path and os.path.exists(audio_path):
            transcription = transcribe_audio(audio_path)
            print("Transcription:", transcription)

        has_image = bool(image_path and os.path.exists(image_path))
        has_audio = bool(transcription and transcription != "Could not transcribe audio")

        prompt_text = f"""You are a world-class multimodal fake news detection expert.

Caption/Text claim: {text or "none provided"}

Audio transcription (what was actually said in the audio, word for word): {transcription or "none provided"}

{"An image is attached below. Look at it carefully." if has_image else "No image was provided."}

Your task has THREE parts. Do ALL that apply:

PART 1 - IMAGE CONSISTENCY CHECK (only if an image is attached):
Does the image actually show what the caption claims? Could this image be an unrelated/recycled image?

PART 2 - AUDIO CONSISTENCY CHECK (only if an audio transcription is provided):
Compare the CAPTION's claim word-by-word against what the audio transcription ACTUALLY says.
Does the audio really say what the caption claims it says? Look for cases where the caption
OVERSTATES, MISQUOTES, or CONTRADICTS the actual spoken words. For example, if the caption says
"announces retirement" but the audio only says "haven't decided yet", this is a MISMATCH and a
strong sign of misinformation, even if no single word is technically false.

PART 3 - OVERALL VERDICT:
Combine the image check AND the audio check to decide FAKE or REAL.
If EITHER the image OR the audio contradicts/fails to support the caption, this is strong
evidence of FAKE (misinformation often works by pairing real content with a false or
exaggerated caption).

Respond in EXACTLY this format:
RELATED: [YES, NO, or N/A] (image vs caption)
RELATED_REASON: [one sentence on why the image does or doesn't match the caption]
AUDIO_MATCH: [YES, NO, or N/A] (does the audio actually support the caption's specific claim?)
AUDIO_MATCH_REASON: [one sentence comparing the caption's claim to what the audio actually says]
VERDICT: [FAKE or REAL]
CONFIDENCE: [a number 0-100]
SOURCE: [specific platforms where this type of content typically spreads]
SPREAD_BY: [specific account/channel types]
EXPLANATION: [2-3 sentences combining the image finding AND the audio finding]

Rules:
- VERDICT must be exactly FAKE or REAL
- If RELATED is NO, or AUDIO_MATCH is NO, VERDICT should usually be FAKE
- SOURCE must name specific platforms, never N/A when VERDICT is FAKE
- The EXPLANATION must explicitly mention the audio finding if audio was provided, not just the image
"""

        content = [{"type": "text", "text": prompt_text}]
        if has_image:
            content.append({
                "type": "image_url",
                "image_url": {"url": _load_image_as_data_url(image_path)},
            })

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=700,
        )
        raw = response.choices[0].message.content
        print("Fusion response:", raw)
        parsed = _parse(raw, transcription)
        return parsed

    except Exception as e:
        print("fusion_service error:", e)
        return _error(str(e), transcription="")


def _parse(raw, transcription=""):
    data = {"verdict": "UNKNOWN", "confidence": "N/A", "related": "N/A",
            "related_reason": "N/A", "audio_match": "N/A", "audio_match_reason": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": "N/A", "transcription": transcription}
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("RELATED_REASON:"):
            data["related_reason"] = line[16:].strip()
        elif line.startswith("RELATED:"):
            data["related"] = line[8:].strip().upper()
        elif line.startswith("AUDIO_MATCH_REASON:"):
            data["audio_match_reason"] = line[20:].strip()
        elif line.startswith("AUDIO_MATCH:"):
            data["audio_match"] = line[12:].strip().upper()
        elif line.startswith("VERDICT:"):
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


def _error(msg, transcription=""):
    return {"verdict": "ERROR", "confidence": "N/A", "related": "N/A",
            "related_reason": "N/A", "audio_match": "N/A", "audio_match_reason": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": msg[:300], "transcription": transcription}