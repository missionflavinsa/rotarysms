import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
print("--- SCRIPT TO FIND SUBJECT BLOCKS AND C-CODES ---")
for i in range(4, 10):
    page = doc[i]
    blocks = page.get_text("blocks")
    words = page.get_text("words")
    
    print(f"\n======== PAGE {i+1} ========")
    for b in blocks:
        text = b[4].lower().replace("\n", " ").strip()
        # Look for standard subject names 
        for s in ["english", "hindi", "marathi", "mathematics", "environmental studies", "art", "physical education", "health & wellness"]:
            if s in text:
                print(f"[{s.upper()}] found at X_center: {(b[0]+b[2])/2:.1f}")
                
    # Print the X coords of 'Term 1'
    term1_xs = set()
    term2_xs = set()
    for w in words:
        if w[4] == "Term":
            # Just grab the X centers
            term1_xs.add((w[0]+w[2])/2)
            
    # Print the X coords of 'C1.1' 
    c11_xs = set()
    for w in words:
        if w[4] == "C1.1":
            c11_xs.add((w[0]+w[2])/2)
            
    print(f"Term 1 X centers: {sorted([round(x,1) for x in term1_xs])}")
    print(f"C1.1 X centers: {sorted([round(x,1) for x in c11_xs])}")
