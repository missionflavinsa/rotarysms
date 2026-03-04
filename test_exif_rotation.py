import urllib.request
from io import BytesIO
from PIL import Image, ImageOps, ExifTags

# Download the specific image the user mentioned
url = "https://drive.google.com/uc?export=download&id=1l6TlMUO2Hb_rCGJ1XcXUHHfN_BaNh8mt"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
img_data = resp.read()

# 1. Check Raw EXIF
img = Image.open(BytesIO(img_data))
print(f"Original Size: {img.size}")

exif_orientation = None
try:
    exif = img._getexif()
    if exif:
        for k, v in exif.items():
            if k in ExifTags.TAGS and ExifTags.TAGS[k] == 'Orientation':
                exif_orientation = v
                break
except Exception as e:
    pass
print(f"Raw EXIF Orientation: {exif_orientation}")

# 2. Run through exif_transpose (what our upload hook does)
img_upright = ImageOps.exif_transpose(img)
print(f"After exif_transpose: {img_upright.size}")

# 3. Check what happens in admin_results.py process_profile_photo_rectangular
from src.views.admin_results import process_profile_photo_rectangular
# Pass pure bytes mock as if it was fetched from Firebase
print("Running through process_profile_photo_rectangular...")
out_bytes = process_profile_photo_rectangular("data:image/jpeg;base64,...mocking", test_img=img_upright.copy())
if out_bytes:
    out_img = Image.open(BytesIO(out_bytes))
    print(f"Final Output Size: {out_img.size}")
else:
    print("Failed processing")

