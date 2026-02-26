import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
page = doc[5] # Page 6

drawings = page.get_drawings()
horizontal_lines = set()

for d in drawings:
    for item in d["items"]:
        if item[0] == "l": # line
            p1, p2 = item[1], item[2]
            # If it's horizontal (y mostly equal)
            if abs(p1.y - p2.y) < 2:
                horizontal_lines.add(round(p1.y, 1))
        elif item[0] == "re": # rect
            r = item[1]
            horizontal_lines.add(round(r.y0, 1))
            horizontal_lines.add(round(r.y1, 1))

y_lines = sorted(list(horizontal_lines))
print("Found horizontal lines Y-coords:", y_lines[:20])

# Let's find boundaries for C1.1
rects = page.search_for("C1.1")
for r in rects:
    cy = (r.y0 + r.y1)/2
    
    # find line immediately above cy
    above = max([y for y in y_lines if y < cy])
    # find line immediately below cy
    below = min([y for y in y_lines if y > cy])
    
    print(f"For C1.1 at Y={cy:.1f}, Cell Top={above}, Cell Bottom={below}, True Center={(above+below)/2:.1f}")
