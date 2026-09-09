import speech_recognition as sr

from app.config import groq_client


def transcribe_audio(audio_path: str) -> str:
    """Return transcribed text or a fallback string."""
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception as e:
        print("transcribe_audio error:", e)
        return "Could not transcribe audio"


def analyze_audio(audio_path: str) -> dict:
    """Transcribe then ask the LLM to fact-check the spoken content."""
    try:
        transcription = transcribe_audio(audio_path)

        prompt = f"""You are an expert at detecting fake audio and misinformation in spoken content.

Transcribed audio: \"{transcription}\"

Respond in EXACTLY this format (no extra lines):
VERDICT: FAKE
CONFIDENCE: 89%
SOURCE: Telegram channels, WhatsApp forwards, YouTube
SPREAD_BY: Anonymous accounts, political groups, bots
EXPLANATION: [Reason the audio is fake or real]
TRANSCRIPTION: {transcription}

Rules:
- VERDICT must be exactly FAKE or REAL
- If REAL → SOURCE = "Verified broadcasters" and SPREAD_BY = "Verified journalists"
"""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        return _parse(response.choices[0].message.content, transcription)

    except Exception as e:
        print("audio_service error:", e)
        return _error(str(e))


# ── helpers ────────────────────────────────────────────────────────────────────

def _parse(raw: str, transcription: str) -> dict:
    data = {"verdict": "UNKNOWN", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": "N/A", "transcription": transcription}
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):       data["verdict"]      = line[8:].strip()
        elif line.startswith("CONFIDENCE:"):  data["confidence"]   = line[11:].strip()
        elif line.startswith("SOURCE:"):      data["source"]       = line[7:].strip()
        elif line.startswith("SPREAD_BY:"):   data["spread_by"]    = line[10:].strip()
        elif line.startswith("EXPLANATION:"): data["explanation"]  = line[12:].strip()
        elif line.startswith("TRANSCRIPTION:"): data["transcription"] = line[14:].strip()
    return data


def _error(msg: str) -> dict:
    return {"verdict": "ERROR", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": msg[:300], "transcription": ""}
