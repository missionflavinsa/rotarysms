import streamlit as st
import os
import glob

@st.cache_data
def get_available_fonts():
    fonts = {
        "Helvetica (Built-in)": "helv",
        "Helvetica Bold (Built-in)": "helv-bo",
        "Helvetica Italic (Built-in)": "helv-ob",
        "Helvetica Bold Italic (Built-in)": "helv-bo",
        "Times Roman (Built-in)": "times-roman",
        "Times Bold (Built-in)": "times-bold",
        "Times Italic (Built-in)": "times-italic",
        "Courier (Built-in)": "courier",
        "Courier Bold (Built-in)": "courier-bold",
        "Courier Italic (Built-in)": "courier-oblique",
        "Symbol (Built-in)": "symbol",
        "ZapfDingbats (Built-in)": "zapfdingbats"
    }
    
    # Load Custom Local TTFs/OTFs safely
    os.makedirs("fonts", exist_ok=True)
    for file_name in os.listdir("fonts"):
        if file_name.lower().endswith((".ttf", ".otf")):
            path = os.path.join("fonts", file_name)
            name = file_name[:-4].replace("-", " ")
            fonts[f"{name} (Custom)"] = path
        
    # Load system TTFs safely
    for path in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        name = os.path.basename(path).replace(".ttf", "").replace("-", " ")
        fonts[f"{name} (System)"] = path
        
    return fonts
