from app.services.fusion_service import analyze_multimodal

tests = [
    # Subtle mismatches - plausible-sounding but wrong context
    ('uploads/IMG_20250607_204422.jpg', 'Photo taken last week at the new city stadium opening', 'MISMATCH'),
    ('uploads/IMG_20251020_223732.jpg', 'A bride on her wedding day in traditional attire', 'MISMATCH'),
    ('uploads/IMG_20250804_161654.jpg', 'Delegates at a United Nations climate summit', 'MISMATCH'),
    ('uploads/pasted_image.png', 'Official portrait released by the Vatican press office', 'MISMATCH'),
    ('uploads/IMG_20260414_161209.jpg', 'A photo shared from a recent protest march downtown', 'MISMATCH'),
    # Genuine matches, described plainly and plausibly
    ('uploads/IMG-20250828-WA0029.jpg', 'Someone spending time in a garden', 'MATCH'),
    ('uploads/IMG_20250502_115534.jpg', 'A casual photo of a person indoors', 'MATCH'),
    ('uploads/IMG_20251102_113426.jpg', 'A simple headshot-style photo', 'MATCH'),
    ('uploads/url_image.jpg', 'A landscape photo shared online', 'MATCH'),
    ('uploads/WhatsApp Image 2026-05-04 at 3.24.06 PM.jpeg', 'A screenshot someone shared of a document template', 'MATCH'),
]

correct = 0
for img, caption, expected in tests:
    r = analyze_multimodal(text=caption, image_path=img)
    got_related = r['related']
    if got_related == 'YES':
        got_label = 'MATCH'
    elif got_related == 'NO':
        got_label = 'MISMATCH'
    else:
        got_label = 'UNCLEAR'

    is_correct = got_label == expected
    correct += is_correct

    print(img)
    print("  caption:", caption)
    print("  expected:", expected, "| got:", got_label, "(" + got_related + ")", "| verdict:", r['verdict'], "| correct:", is_correct)
    print()

print("TOTAL:", correct, "/", len(tests), "correct =", round(correct / len(tests) * 100, 1), "%")