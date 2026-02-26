from src.views.admin_results import process_profile_photo_original, get_original_shape_mask
import fitz

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]

# Let's test the blob finder
blob_path = None
for p in page.get_drawings():
    fill = p.get("fill")
    if fill and fill[0] > 0.5 and fill[1] < 0.5 and fill[2] < 0.5:
        blob_path = p
        break

if blob_path:
    print(f"Found blob. Rect: {blob_path['rect']}")
else:
    print("No blob found!")

# Let's test the target rect
print("Target Rect defined in code:", fitz.Rect(378.49 + 2, 218.93 + 2, 583.43 - 2, 493.02 - 2))
