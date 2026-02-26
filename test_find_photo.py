import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]

drawings = page.get_drawings()
for i, d in enumerate(drawings):
    r = d['rect']
    area = (r.x1 - r.x0) * (r.y1 - r.y0)
    if area > 10000 and d.get('fill'):
        fill = d.get('fill')
        # Check if R is strictly greater than G and B
        if len(fill) == 3 and fill[0] > fill[1] and fill[0] > fill[2]:
            print(f"Candidate Shape {i}: Rect: {r}, Fill: {fill}, Area: {area}")
            
# Save an image of page 2 to check
pix = page.get_pixmap()
pix.save("page2.png")
