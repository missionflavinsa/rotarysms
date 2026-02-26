import fitz

doc = fitz.open("test_photo_output.pdf")
page = doc[1]
pix = page.get_pixmap(dpi=150)
pix.save("test_photo_render.png")
print("Rendered PDF Page 2 to test_photo_render.png")
