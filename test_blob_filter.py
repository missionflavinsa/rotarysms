import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]
paths = page.get_drawings()

print("Checking shapes matching the RED criteria:")
for i, p in enumerate(paths):
    fill = p.get("fill")
    if fill and fill[0] > 0.5 and fill[1] < 0.5 and fill[2] < 0.5:
        print(f"Index {i}, Rect: {p['rect']}, Fill: {fill}")
