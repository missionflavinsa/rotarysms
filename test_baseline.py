import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]

# Extract dict info spanning text
blocks = page.get_text("dict")["blocks"]
labels = ["Name of the Learner", "APAAR ID/PEN", "Registration Number", "Roll No", "Class & Section", "Date of Birth", "Class Teacher", "Name of Mother", "Name of Father"]

print(f"{'Label':<25} | {'Y0 (Top)':<10} | {'Y1 (Bottom)':<10} | {'X1 (Right)':<10}")
print("-" * 65)

for b in blocks:
    if "lines" in b:
        for line in b["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                for l in labels:
                    if l in text:
                        # span["origin"] gives the (x, y) coordinates of the text baseline!
                        print(f"{l:<25} | {span['bbox'][1]:.1f}      | {span['bbox'][3]:.1f}      | {span['bbox'][2]:.1f}")
                        print(f"  -> Exact Baseline Origin Y: {span['origin'][1]:.1f}")
