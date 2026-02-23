import fitz

doc = fitz.open('tempalates/Progress 3rd to 5th 2026.pdf')
page = doc[2] # Page 3

blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if "lines" in b:
        for l in b["lines"]:
            for span in l["spans"]:
                if span["text"].strip():
                    print(f"Text: '{span['text']}' at {span['bbox']}")

