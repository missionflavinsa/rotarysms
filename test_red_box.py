import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1] # Page 2

drawings = page.get_drawings()
for i, d in enumerate(drawings):
    r = d['rect']
    area = (r.x1 - r.x0) * (r.y1 - r.y0)
    if area > 1000 and d.get('fill'):
        fill = d.get('fill')
        print(f"SHAPE: Drawing {i} Rect: {r} Fill: {fill} Area: {area}")
