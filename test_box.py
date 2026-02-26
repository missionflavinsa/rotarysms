import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")

# We'll just test on Page 6 for C1.1 
page = doc[5]
rects = page.search_for("C1.1")
# For Page 6 Left, the term X centers are ~465 and ~524.5
t1_center = 465.2

for r in rects:
    if r.x0 < 595: # Left table
        # We'll draw 3 different variations to see what centers perfectly
        
        # Test 1: Just textbox horizontal center
        rect1 = fitz.Rect(t1_center - 25, r.y0, t1_center + 25, r.y1)
        page.draw_rect(rect1, color=(1,0,0)) # red box
        page.insert_textbox(rect1, "B", fontsize=11, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)
        
        # Test 2: Calculate precise baseline using 0.35
        cy = (r.y0 + r.y1) / 2.0
        # What was the term 2 center? 524.5
        t2_center = 524.5
        rect2 = fitz.Rect(t2_center - 25, r.y0, t2_center + 25, r.y1)
        page.draw_rect(rect2, color=(0,0,1))
        
        y_pos = cy + (11 * 0.3)
        # Using string length offset
        length_offset = len("Co") * 11 * 0.28
        page.insert_text((t2_center - length_offset, y_pos), "Co", fontsize=11, fontname="helv", color=(0,0,1))
        
doc.save("test_out.pdf")
print("Saved to test_out.pdf")
