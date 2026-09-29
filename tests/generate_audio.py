import pyttsx3

engine = pyttsx3.init()

clips = {
    "uploads/tts_clip1.wav": "The government has announced a new tax policy that will take effect next year.",
    "uploads/tts_clip2.wav": "Scientists at the university confirmed the vaccine trial results were successful.",
    "uploads/tts_clip3.wav": "The mayor said the new bridge project has been delayed by six months.",
    "uploads/tts_clip4.wav": "The company reported a decline in profits during the last quarter.",
}

for path, text in clips.items():
    engine.save_to_file(text, path)

engine.runAndWait()
print("Done. Generated:", list(clips.keys()))