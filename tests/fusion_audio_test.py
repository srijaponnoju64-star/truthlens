from app.services.fusion_service import analyze_multimodal

result = analyze_multimodal(
    text="Breaking: Famous cricketer announces retirement in this exclusive audio message",
    image_path="uploads/IMG_20250607_204422.jpg",  # unrelated image on purpose
    audio_path="uploads/dhoni.m4a",
)

print("VERDICT:", result["verdict"])
print("CONFIDENCE:", result["confidence"])
print("RELATED:", result["related"])
print("RELATED_REASON:", result.get("related_reason", "N/A"))
print("TRANSCRIPTION:", result["transcription"][:200])
print("EXPLANATION:", result["explanation"])