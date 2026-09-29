from app.services.fusion_service import analyze_multimodal

tests = [
    # dhoni.m4a really says: "...nothing to decide as of now..." (about retirement)
    ("uploads/dhoni.m4a", "Cricketer says he has not yet decided when he will retire", "YES"),
    ("uploads/dhoni.m4a", "Cricketer officially announces his retirement from all cricket", "NO"),
    ("uploads/dhoni.m4a", "43-year-old player says he still loves the affection he receives from fans", "YES"),
    ("uploads/dhoni.m4a", "Player confirms he is quitting IPL immediately due to injury", "NO"),
    ("uploads/dhoni.m4a", "Speaker mentions playing only two months a year during IPL", "YES"),

    # virat avnitha.m4a really says something about Virat Kohli and a photo, not liking her
    ("uploads/virat avnitha.m4a", "Audio discusses Virat Kohli's reaction to a photo involving Avneet Kaur", "YES"),
    ("uploads/virat avnitha.m4a", "Virat Kohli announces he is getting married to Avneet Kaur", "NO"),
    ("uploads/virat avnitha.m4a", "Virat Kohli expresses that he does not like something related to Avneet Kaur", "YES"),
]

correct = 0
for audio, caption, expected in tests:
    r = analyze_multimodal(text=caption, image_path=None, audio_path=audio)
    got = r["audio_match"]
    is_correct = got == expected
    correct += is_correct
    print(audio, "|", caption)
    print("  expected:", expected, "| got:", got, "| verdict:", r["verdict"], "| correct:", is_correct)
    print("  reason:", r.get("audio_match_reason", "N/A"))
    print()

print("TOTAL:", correct, "/", len(tests), "correct =", round(correct / len(tests) * 100, 1), "%")