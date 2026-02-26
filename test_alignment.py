import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1] 

# Draw red dots at the current insertion coordinates to see where they land
coords = {
    "Name": (180, 245),
    "APAAR": (150, 280),
    "Reg No": (250, 315),
    "Roll No": (100, 350),
    "Class": (150, 387),
    "DOB": (130, 422),
    "Teacher": (140, 458),
    "Mother": (150, 496),
    "Father": (150, 532)
}

for label, (x, y) in coords.items():
    page.draw_circle((x, y), 3, color=(1,0,0), fill=(1,0,0))
    page.insert_text((x+5, y), label, fontsize=8, color=(1,0,0))
    
doc.save("test_alignment.pdf")
print("Saved visualization to test_alignment.pdf")
