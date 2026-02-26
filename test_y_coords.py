import fitz
import json

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
pages_meta = {}

for i in range(4, 10):
    page = doc[i]
    words = page.get_text("words")
    
    # We want to catalog every C-code in the page
    c_codes = {}
    
    # We also want to find the precise Term 1 and Term 2 X-coords for each table
    term_xs = []
    
    for w in words:
        text = w[4]
        # if it's a C-code like C1.1, C2.2, C5.2
        if len(text) == 4 and text.startswith("C") and text[1].isdigit() and text[2] == '.' and text[3].isdigit():
            x_center = (w[0] + w[2]) / 2
            y_center = (w[1] + w[3]) / 2
            
            # Determine if this is the LEFT table or RIGHT table
            side = "Left" if x_center < 595 else "Right"
            
            if side not in c_codes:
                c_codes[side] = {}
            c_codes[side][text] = round(y_center, 1)
            
        elif text == "Term":
            x_center = (w[0] + w[2]) / 2
            term_xs.append(x_center)
            
    # Sort term_xs and assign to side
    mapped_terms = {"Left": {"T1": None, "T2": None}, "Right": {"T1": None, "T2": None}}
    left_terms = sorted([x for x in term_xs if x < 595])
    right_terms = sorted([x for x in term_xs if x > 595])
    
    # Usually there are 2 terms per table (Term 1, Term 2) or more. We want the two X coordinates.
    # On page 10 there's a bunch of "Term" (e.g. for Term over Term) so we just take the first two unique X's.
    def get_top_two(lst):
        unique = []
        for x in lst:
            if not any(abs(x - ux) < 10 for ux in unique):
                unique.append(x)
        return unique[:2]
        
    l2 = get_top_two(left_terms)
    r2 = get_top_two(right_terms)
    if len(l2) == 2:
        mapped_terms["Left"]["T1"] = round(l2[0], 1)
        mapped_terms["Left"]["T2"] = round(l2[1], 1)
    if len(r2) == 2:
        mapped_terms["Right"]["T1"] = round(r2[0], 1)
        mapped_terms["Right"]["T2"] = round(r2[1], 1)
        
    pages_meta[f"Page {i+1}"] = {
        "C_Codes": c_codes,
        "Terms": mapped_terms
    }

print(json.dumps(pages_meta, indent=2))
