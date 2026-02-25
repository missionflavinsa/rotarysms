import fitz
import io
from PIL import Image

def get_blob_mask():
    doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")
    page = doc[2]
    paths = page.get_drawings()
    
    blob_path = None
    for p in paths:
        fill = p.get("fill")
        if fill and fill[0] > 0.5 and fill[1] < 0.5 and fill[2] < 0.5:
            blob_path = p
            break
            
    if not blob_path:
        print("Blob not found")
        return
        
    rect = blob_path["rect"]
    print(f"Original rect: {rect}")
    
    # Create a new blank PDF page of the exact size of the rect
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=rect.width, height=rect.height)
    
    # We want to draw the blob path exactly at (0,0). So we must translate it.
    offset_x = -rect.x0
    offset_y = -rect.y0
    
    shape = out_page.new_shape()
    for item in blob_path["items"]:
        cmd = item[0]
        if cmd == "l":
            shape.draw_line(item[1] + (offset_x, offset_y), item[2] + (offset_x, offset_y))
        elif cmd == "c":
            shape.draw_bezier(item[1] + (offset_x, offset_y), item[2] + (offset_x, offset_y), 
                              item[3] + (offset_x, offset_y), item[4] + (offset_x, offset_y))
        elif cmd == "re":
            shape.draw_rect(item[1] + fitz.Rect(offset_x, offset_y, offset_x, offset_y))
        elif cmd == "qu":
            shape.draw_quad(item[1] + fitz.Quad(offset_x, offset_y, offset_x, offset_y))
            
    # We want it to be pure white fill (which will be the mask) on black background
    out_page.draw_rect(out_page.rect, color=(0,0,0), fill=(0,0,0))
    shape.finish(color=(1,1,1), fill=(1,1,1))
    shape.commit()
    
    pix = out_page.get_pixmap(dpi=300)
    pix.save("blob_mask.png")
    print("Saved blob_mask.png")
    
get_blob_mask()
