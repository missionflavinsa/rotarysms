import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
print("--- SCRIPT TO FIND 'Term 1' COORDS ---")
for i in range(4, 10):
    page = doc[i]
    words = page.get_text("words")
    for w in words:
        if "Term" in w[4]:
            print(f"Page {i+1} found 'Term': Rect(x0={w[0]:.1f}, y0={w[1]:.1f}, x1={w[2]:.1f}, y1={w[3]:.1f})")
    
    # Also find C1.1, C1.2 to verify Y-coords
    for w in words:
        if w[4] in ["C1.1", "C1.2", "C5.1"]:
            print(f"Page {i+1} found '{w[4]}': Rect(x0={w[0]:.1f}, y0={w[1]:.1f}, x1={w[2]:.1f}, y1={w[3]:.1f})")

