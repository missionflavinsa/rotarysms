import fitz

doc = fitz.open('tempalates/Progress 3rd to 5th 2026.pdf')
# Let's check Page 2 (index 1) and Page 3 (index 2) again
for p_num in [1, 2]:
    print(f"\n--- PAGE {p_num + 1} ---")
    page = doc[p_num]
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if "lines" in b:
            for l in b["lines"]:
                for span in l["spans"]:
                    if any(word in span["text"].lower() for word in ["mother", "father", "parent"]):
                        print(f"Text: '{span['text']}' at {span['bbox']}")
