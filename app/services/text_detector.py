import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "Sree6464/truthlens-textonly-model"
THRESHOLD = 0.6

_tokenizer = None
_model = None


def _load_model(max_retries: int = 3):
    """Load the tokenizer and model on first use, with retries.
    Loading lazily (instead of at import time) means a slow start
    or a single network hiccup on the hosting platform won't crash
    the whole app before it even starts."""
    global _tokenizer, _model
    if _model is not None:
        return

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            _model.eval()
            return
        except Exception as e:
            last_error = e
            print(f"text_detector: model load attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(3 * attempt)

    raise RuntimeError(f"Could not load text classifier after {max_retries} attempts: {last_error}")


def predict_text(statement: str) -> dict:
    try:
        _load_model()
        inputs = _tokenizer(statement, return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            logits = _model(**inputs).logits
        prob_real = torch.softmax(logits, dim=-1)[0][1].item()

        verdict = "REAL" if prob_real >= THRESHOLD else "FAKE"
        confidence = prob_real if verdict == "REAL" else 1 - prob_real
        return {"verdict": verdict, "confidence": confidence}

    except Exception as e:
        print("text_detector error, falling back to neutral:", e)
        # If the trained classifier truly can't load, don't crash the
        # whole text module — fall back to a neutral signal so the
        # evidence-grounded LLM step can still run and decide alone.
        return {"verdict": "REAL", "confidence": 0.5}