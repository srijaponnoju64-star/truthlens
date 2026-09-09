from app.config import groq_client


def analyze_text(text: str, source_url: str = None) -> dict:
    try:
        url_context = f"This content was fetched from URL: {source_url}\n\n" if source_url else ""

        prompt = f"""{url_context}You are a world-class fake news and misinformation detection expert.

Analyze this text carefully:
\"\"\"{text[:2000]}\"\"\"

You MUST respond in EXACTLY this format (no extra lines):
VERDICT: FAKE
CONFIDENCE: 94%
SOURCE: WhatsApp groups, Facebook pages, Telegram channels
SPREAD_BY: Political bot networks, anonymous forwarders, clickbait channels
EXPLANATION: This claim is false because [specific reason]. Fact-checking organisations have debunked similar claims.

Rules:
- VERDICT must be exactly FAKE or REAL
- SOURCE must name specific platforms
- SPREAD_BY must name specific account types
- If REAL → SOURCE = "Verified news outlets: BBC, NDTV, Reuters"  and  SPREAD_BY = "Verified journalists and official accounts"
- NEVER put N/A for SOURCE when content is FAKE
"""

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        return _parse(response.choices[0].message.content)

    except Exception as e:
        print("text_service error:", e)
        return _error(str(e))


# ── helpers ────────────────────────────────────────────────────────────────────

def _parse(raw: str) -> dict:
    data = {"verdict": "UNKNOWN", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A", "explanation": "N/A"}
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):    data["verdict"]     = line[8:].strip()
        elif line.startswith("CONFIDENCE:"): data["confidence"] = line[11:].strip()
        elif line.startswith("SOURCE:"):   data["source"]      = line[7:].strip()
        elif line.startswith("SPREAD_BY:"): data["spread_by"]  = line[10:].strip()
        elif line.startswith("EXPLANATION:"): data["explanation"] = line[12:].strip()
    return data


def _error(msg: str) -> dict:
    return {"verdict": "ERROR", "confidence": "N/A",
            "source": "N/A", "spread_by": "N/A",
            "explanation": msg[:300]}
