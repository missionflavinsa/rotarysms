import sys
sys.path.append("/home/austinroyster/MEGA/Webapps/result management system")

import fitz
from src.views.admin_results import process_profile_photo_original

print("Starting photo test...")
# Test dummy image
dummy_url = "https://www.w3schools.com/w3images/avatar2.png" 

doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
page = doc[1]

try:
    processed_img_bytes, target_rect = process_profile_photo_original(dummy_url)
    if processed_img_bytes and target_rect:
        page.insert_image(target_rect, stream=processed_img_bytes)
        doc.save("test_photo_output.pdf")
        print("Successfully saved test_photo_output.pdf!")
    else:
        print("process_profile_photo_original returned None")
except Exception as e:
    import traceback
    traceback.print_exc()
