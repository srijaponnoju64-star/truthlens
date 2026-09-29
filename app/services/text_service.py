from app.config import groq_client
from app.services.text_detector import predict_text
from app.services.evidence_retriever import get_evidence, format_evidence_for_prompt


def analyze_text(text: str, source_url: str = None) -> dict:
    try:
        # Step 1: Trained classifier's opinion
        model_result = predict_text(text)
        model_verdict = model_result["verdict"]
        model_confidence_pct = round(model_result["confidence"] * 100, 1)

        # Step 2: Retrieve real web evidence about this claim
        evidence = get_evidence(text)
        evidence_text = format_evidence_for_prompt(evidence)

        # Step 3: LLM verifies against actual evidence, not memory alone
        url_context = f"This content was fetched from URL: {source_url}\n\n" if source_url else ""

        prompt = f"""{url_context}Verify this claim using the web evidence provided below. Base your verdict on the evidence, not general assumptions.

CLAIM:
\"\"\"{text[:2000]}\"\"\"

WEB EVIDENCE:
{evidence_text}

Respond in EXACTLY this format (no extra lines):
LLM_VERDICT: [REAL or FAKE]
LLM_CONFIDENCE: [a number 0-100, how sure you are based on the evidence]
SOURCE: [specific platforms where this type of content typically spreads, if FAKE]
SPREAD_BY: [specific account/channel types, if FAKE]
EXPLANATION: [reference the evidence above directly to justify your verdict]

Rules:
- Do NOT flag commonly-understood, everyday statements as FAKE just because a stricter technical reading exists (e.g. "the sun rises in the east" is TRUE in common usage, even though astronomically it varies by season). Only mark FAKE if the claim is misleading in a way that actually matters or spreads false information.
- If evidence is insufficient or contradictory, say so honestly in EXPLANATION and give your best-supported verdict, with a lower LLM_CONFIDENCE
- If LLM_VERDICT is REAL → SOURCE = "Verified news outlets: BBC, NDTV, Reuters" and SPREAD_BY = "Verified journalists and official accounts"
- If LLM_VERDICT is FAKE → name specific platforms (WhatsApp groups, Facebook pages, Telegram channels) and specific spreader types
"""

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
            reasoning_effort="low",
        )

        raw_response = response.choices[0].message.content
        parsed = _parse_full(raw_response)

        if parsed["source"] == "N/A" and parsed["spread_by"] == "N/A" and parsed["explanation"] == "N/A":
            print("=== PARSE FAILURE — RAW LLM RESPONSE ===")
            print(raw_response)
            print("=========================================")

        llm_verdict = parsed.get("llm_verdict", "UNKNOWN")
        llm_confidence_pct = parsed.get("llm_confidence")

        # Final verdict: evidence-grounded LLM takes priority.
        # The confidence reported must always match whichever verdict wins.
        if llm_verdict in ("REAL", "FAKE"):
            final_verdict = llm_verdict
            if llm_confidence_pct is not None:
                confidence_pct = llm_confidence_pct
            else:
                confidence_pct = model_confidence_pct if llm_verdict == model_verdict else "N/A"
            if llm_verdict != model_verdict:
                final_verdict += " (evidence-verified)"
        else:
            final_verdict = model_verdict
            confidence_pct = model_confidence_pct

        confidence_str = f"{confidence_pct}%" if confidence_pct != "N/A" else "N/A"

        return {
            "verdict": final_verdict,
            "confidence": confidence_str,
            "source": parsed["source"],
            "spread_by": parsed["spread_by"],
            "explanation": parsed["explanation"],
        }

    except Exception as e:
        print("text_service error:", e)
        return _error(str(e))


def _parse_full(raw: str) -> dict:
    data = {"llm_verdict": "UNKNOWN", "llm_confidence": None,
            "source": "N/A", "spread_by": "N/A", "explanation": "N/A"}
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("LLM_VERDICT:"):
            data["llm_verdict"] = line[12:].strip().upper()
        elif line.startswith("LLM_CONFIDENCE:"):
            digits = "".join(c for c in line[15:] if c.isdigit() or c == ".")
            try:
                data["llm_confidence"] = round(float(digits), 1) if digits else None
            except ValueError:
                data["llm_confidence"] = None
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