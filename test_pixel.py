from PIL import Image

img = Image.open('test_photo_render.png')
# Check center pixel of the red blob in the rendered image
# Rect(378.49, 218.93, 583.42, 493.02)
# At 150 DPI, coordinates scale by 150/72 = ~2.0833
scale = 150/72
x = int((378.49 + 583.42) / 2 * scale)
y = int((218.93 + 493.02) / 2 * scale)

pixel = img.getpixel((x, y))
print(f"Center Pixel at rendered ({x}, {y}) is: {pixel}")
if pixel[0] > 200 and pixel[1] < 100 and pixel[2] < 100:
    print("ANALYSIS: Avatar is HIDDEN behind the red blob.")
else:
    print("ANALYSIS: Avatar is ON TOP.")
