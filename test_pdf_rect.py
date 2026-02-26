import fitz
doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
for i in range(4, 10):
    page = doc[i]
    print(f"Page {i+1} rect: {page.rect}")
