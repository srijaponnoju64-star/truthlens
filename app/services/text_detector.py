from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "Sree6464/truthlens-textonly-model"
THRESHOLD = 0.6

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

def predict_text(statement: str) -> dict:
    inputs = tokenizer(statement, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
    prob_real = torch.softmax(logits, dim=-1)[0][1].item()

    verdict = "REAL" if prob_real >= THRESHOLD else "FAKE"
    confidence = prob_real if verdict == "REAL" else 1 - prob_real

    return {"verdict": verdict, "confidence": confidence}