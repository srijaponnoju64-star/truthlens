import time
import requests
from app.config import SERPER_API_KEY

SERPER_URL = "https://google.serper.dev/search"


def get_evidence(claim: str, max_results: int = 5, max_retries: int = 3) -> list[dict]:
    """
    Searches the web via Serper.dev (Google Search API) for real evidence related to a claim.
    Returns a list of {title, snippet, url} dicts from actual search results.
    Retries on timeout/connection errors before giving up.
    """
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": claim, "num": max_results}

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            evidence = []
            for item in data.get("organic", [])[:max_results]:
                evidence.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                })
            return evidence

        except Exception as e:
            last_error = e
            print(f"evidence_retriever error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)  # wait 5s, then 10s before retrying

    print("evidence_retriever: giving up after retries:", last_error)
    return []


def format_evidence_for_prompt(evidence: list[dict]) -> str:
    """
    Turns retrieved evidence into readable text for the LLM prompt.
    """
    if not evidence:
        return "No web evidence could be retrieved for this claim."

    lines = []
    for i, item in enumerate(evidence, 1):
        lines.append(f"[{i}] {item['title']}\n{item['snippet']}\nSource: {item['url']}")
    return "\n\n".join(lines)