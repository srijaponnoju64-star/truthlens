import os
from app.config import groq_client
from app.services.audio_service import transcribe_audio


def analyze_multimodal(text=None, image_path=None, audio_path=None):
    try:
        transcription = ""
        if audio_path and os.path.exists(audio_path):
            transcription = transcribe_audio(audio_path)
            print("Transcription:", transcription)

        prompt = f"""You are a world-class multimodal fake news detection expert.

Analyze this social media content:
Caption/Text: {text or "none provided"}
Audio transcription: {transcription or "none provided"}
Image filename: {os.path.basename(image_path) if image_path else "none"}

Determine if this is FAKE or REAL news.

Respond in EXACTLY this format:
VERDICT: FAKE
CONFIDENCE: 92%
SOURCE: WhatsApp forwards, Facebook, Telegram
SPREAD_BY: Anonymous accounts, political bots
EXPLANATION: The caption makes extraordinary claims that cannot be verified by any credible source. This type of content is commonly shared to spread misinformation on social media platforms.

Rules:
- VERDICT must be exactly FAKE or REAL
- If text makes extraordinary unverifiable claims = FAKE
- If content is genuine and verifiable = REAL
- SOURCE must name specific platforms
- EXPLANATION must be 2-3 sentences"""

        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        raw = response.choices[0].message.content
        print("Fusion response:", raw)
        parsed = _parse(raw, transcription)
        parsed["related"] = "YES" if transcription else "N/A"
        return parsed

    except Exception as e:
        print("fusion_service error:", e)
        return _error(str(e))


def _parse(raw, transcription=""):
    data = {"verdict": "UNKNOWN", "confidence": "N/A", "related": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": "N/A", "transcription": transcription}
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):
            data["verdict"] = line[8:].strip()
        elif line.startswith("CONFIDENCE:"):
            data["confidence"] = line[11:].strip()
        elif line.startswith("SOURCE:"):
            data["source"] = line[7:].strip()
        elif line.startswith("SPREAD_BY:"):
            data["spread_by"] = line[10:].strip()
        elif line.startswith("EXPLANATION:"):
            data["explanation"] = line[12:].strip()
        elif line.startswith("RELATED:"):
            data["related"] = line[8:].strip()
    return data


def _error(msg, transcription=""):
    return {"verdict": "ERROR", "confidence": "N/A", "related": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": msg[:300], "transcription": transcription}