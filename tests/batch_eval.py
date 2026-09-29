import sys
import time
import json
from collections import Counter

sys.path.append(".")

from app.services.text_service import analyze_text
from datasets import load_dataset

SAMPLE_SIZE = 150       # same 150 items as before, so results can be compared
DELAY_SECONDS = 3       # wait between items (was 1 second)
MAX_RETRIES = 3         # tries per item
RETRY_WAIT = 30         # seconds to wait before trying again
STOP_AFTER_FAILS = 5    # stop if this many items in a row fail
OUT_FILE = "batch_eval_results_v2.json"

print("Loading test dataset...")
dataset = load_dataset("chengxuphd/liar2")
test_set = dataset["test"]


def to_binary_label(label):
    return "FAKE" if label in [0, 1, 2] else "REAL"


def get_pred(verdict):
    if "FAKE" in verdict:
        return "FAKE"
    if "REAL" in verdict:
        return "REAL"
    return "ERROR"


results = []
fails_in_a_row = 0
total = min(SAMPLE_SIZE, len(test_set))

for i in range(total):
    statement = test_set[i]["statement"]
    true_label = to_binary_label(test_set[i]["label"])

    result = None
    pred = "ERROR"
    for attempt in range(1, MAX_RETRIES + 1):
        result = analyze_text(statement)
        pred = get_pred(result["verdict"])
        if pred != "ERROR":
            break
        print(f"  item {i} attempt {attempt} failed: {result['explanation'][:150]}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_WAIT)

    results.append({
        "index": i,
        "statement": statement,
        "true": true_label,
        "pred": pred,
        "correct": pred == true_label,
        "error_message": result["explanation"] if pred == "ERROR" else "",
    })

    # save after every item so nothing is lost
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    if pred == "ERROR":
        fails_in_a_row += 1
        if fails_in_a_row >= STOP_AFTER_FAILS:
            print(f"\nStopped: {STOP_AFTER_FAILS} items failed in a row.")
            print("Probably a daily/minute limit. Wait some time and run again.")
            break
    else:
        fails_in_a_row = 0

    if i % 10 == 0:
        ok = [r for r in results if r["pred"] != "ERROR"]
        good = sum(1 for r in ok if r["correct"])
        print(f"Processed {i + 1}/{total} - working items: {len(ok)}, correct: {good}")

    time.sleep(DELAY_SECONDS)

# ---------- Final report ----------
valid = [r for r in results if r["pred"] != "ERROR"]
errors = [r for r in results if r["pred"] == "ERROR"]

tp = sum(1 for r in valid if r["true"] == "FAKE" and r["pred"] == "FAKE")
tn = sum(1 for r in valid if r["true"] == "REAL" and r["pred"] == "REAL")
fp = sum(1 for r in valid if r["true"] == "REAL" and r["pred"] == "FAKE")
fn = sum(1 for r in valid if r["true"] == "FAKE" and r["pred"] == "REAL")

precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

print("\n=== FINAL RESULTS ===")
print(f"Items tried:      {len(results)}")
print(f"Items that worked: {len(valid)}")
print(f"Items with ERROR:  {len(errors)}")
if valid:
    print(f"Accuracy (working items only): {(tp + tn) / len(valid) * 100:.2f}%")
print(f"Accuracy (errors counted wrong): {(tp + tn) / len(results) * 100:.2f}%")
print(f"Confusion matrix: TP={tp} TN={tn} FP={fp} FN={fn}")
print(f"Precision (FAKE): {precision * 100:.2f}%")
print(f"Recall (FAKE):    {recall * 100:.2f}%")
print(f"F1 (FAKE):        {f1 * 100:.2f}%")

if errors:
    print("\nMost common error messages:")
    for msg, count in Counter(e["error_message"][:120] for e in errors).most_common(5):
        print(f"  {count} x  {msg}")

print(f"\nDetailed results saved to {OUT_FILE}")