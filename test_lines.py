import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1] 

# 1. Let's find exactly where the labels are physically printed
blocks = page.get_text("blocks")
labels = ["Name of the Learner", "APAAR ID/PEN", "Registration", "Roll No", "Class & Section", "Date of Birth", "Class Teacher", "Name of Mother", "Name of Father"]

print("LABEL COORDINATES:")
label_y_coords = []
for b in blocks:
    text = b[4].strip()
    for l in labels:
        if l in text:
            print(f"'{l}' -> Y0: {b[1]:.1f}, X1(End): {b[2]:.1f}")
            label_y_coords.append((b[1], b[3])) # y0, y1

# 2. Let's find the dotted lines (if they are vectors) to get the exact X start and Y baseline
print("\nVECTOR DOT LINES:")
drawings = page.get_drawings()
for d in drawings:
    for item in d["items"]:
        if item[0] == "l": # line
            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) < 2 and p1.y > 200 and p1.y < 600 and p1.x > 100:
                print(f"Horizontal Line at Y: {p1.y:.1f}, from X={p1.x:.1f} to X={p2.x:.1f}")
