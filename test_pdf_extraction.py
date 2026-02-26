import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
for i in range(4, 10):
    page = doc[i]
    text = page.get_text("text").lower().replace("\n", " ")
    print(f"--- PAGE {i+1} ---")
    print(text[:200]) # Print first 200 chars to see if 'english' is there
    print(text[-200:])
