import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1] # Page 2
blocks = page.get_text("blocks")
for b in blocks:
    if "photo" in b[4].lower() or "picture" in b[4].lower() or "stamp" in b[4].lower():
        print(f"TEXT: {b[4]} at {b[:4]}")
