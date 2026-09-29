from app.services.fusion_service import analyze_multimodal

tests = [
    # clip1 really says: government announced a new tax policy, takes effect NEXT YEAR
    ("uploads/tts_clip1.wav", "Government announces new tax policy set to begin next year", "YES"),
    ("uploads/tts_clip1.wav", "Government announces the tax policy has already taken effect this month", "NO"),

    # clip2 really says: scientists confirmed vaccine trial results were successful
    ("uploads/tts_clip2.wav", "University scientists confirm the vaccine trial was successful", "YES"),
    ("uploads/tts_clip2.wav", "University scientists announce the vaccine trial has failed completely", "NO"),

    # clip3 really says: mayor said new bridge project delayed by six months
    ("uploads/tts_clip3.wav", "Mayor announces bridge project delay of six months", "YES"),
    ("uploads/tts_clip3.wav", "Mayor confirms the bridge project is fully completed and open", "NO"),

    # clip4 really says: company reported a decline in profits last quarter
    ("uploads/tts_clip4.wav", "Company reports a decline in profits for the last quarter", "YES"),
    ("uploads/tts_clip4.wav", "Company announces record-breaking profits for the last quarter", "NO"),
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