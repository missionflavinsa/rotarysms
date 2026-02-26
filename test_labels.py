import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]

# Extract all text blocks on Page 2
blocks = page.get_text("blocks")
# Sort by y0 (top coordinate)
blocks.sort(key=lambda b: b[1])

for b in blocks:
    text = b[4].strip()
    if text:
        print(f"Y0: {b[1]:.1f}, Text: {text[:60]}")
