import base64
from io import BytesIO
from PIL import Image

def process_uploaded_image(uploaded_file):
    """
    Reads a Streamlit uploaded file (like a photo), 
    compresses it slightly, and returns the base64 encoded string.
    """
    if not uploaded_file:
        return ""
    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)
        
        # Remove alpha channel if saving as JPEG
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        buffer = BytesIO()
        # Quality can be tweaked, 85 is usually a good balance of size vs quality
        image.save(buffer, format="JPEG", quality=85)
        
        return base64.b64encode(buffer.getvalue()).decode()
        
    except Exception as e:
        print(f"Image processing failed: {e}")
        # Fallback to direct conversion if PIL fails
        uploaded_file.seek(0)
        return base64.b64encode(uploaded_file.getvalue()).decode()
