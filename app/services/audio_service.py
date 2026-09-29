import os
import tempfile
import speech_recognition as sr

from app.config import groq_client

TEXT_MODEL = "openai/gpt-oss-20b"


def _convert_to_wav(audio_path: str) -> str:
    """Convert any audio format (m4a, mp3, etc.) to a temporary WAV file."""
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == ".wav":
        return audio_path

    from moviepy import AudioFileClip
    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    clip = AudioFileClip(audio_path)
    clip.write_audiofile(tmp_wav, logger=None)
    clip.close()
    return tmp_wav


def transcribe_audio(audio_path: str) -> str:
    """Return transcribed text or a fallback string."""
    wav_path = None
    try:
        wav_path = _convert_to_wav(audio_path)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception as e:
        print("transcribe_audio error:", e)
        return "Could not transcribe audio"
    finally:
        # clean up the temp wav file if we created one
        if wav_path and wav_path != audio_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


def analyze_audio(audio_path: str) -> dict:
    """Transcribe then ask the LLM to fact-check the spoken content."""
    try:
        transcription = transcribe_audio(audio_path)

        prompt = f"""You are an expert at detecting fake audio and misinformation in spoken content.

Transcribed audio: "{transcription}"

Respond in EXACTLY this format (no extra lines):
VERDICT: FAKE
CONFIDENCE: 89%
SOURCE: Telegram channels, WhatsApp forwards, YouTube
SPREAD_BY: Anonymous accounts, political groups, bots
EXPLANATION: [Reason the audio is fake or real]
TRANSCRIPTION: {transcription}

Rules:
- VERDICT must be exactly FAKE or REAL
- If REAL -> SOURCE = "Verified broadcasters" and SPREAD_BY = "Verified journalists"
"""

        response = groq_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        return _parse(response.choices[0].message.content, transcription)

    except Exception as e:
        print("audio_service error:", e)
        return _error(str(e))


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