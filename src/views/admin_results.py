import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import os
import glob
import base64
import requests
import zipfile
from PIL import Image, ImageDraw
from src.database.firebase_init import get_all_classes, get_students_by_class, get_all_users

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

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

def process_profile_photo_rectangular(image_source, target_size=(201, 274)):
        if image_source.startswith("http://") or image_source.startswith("https://"):
            resp = requests.get(image_source, timeout=5)
            img_data = resp.content
        else:
            if "base64," in image_source:
                image_source = image_source.split("base64,")[1]
            img_data = base64.b64decode(image_source)
            
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        w, h = img.size
        target_ratio = target_size[0] / target_size[1]
        img_ratio = w / h
        
        if img_ratio > target_ratio:
            new_w = int(target_ratio * h)
            left = (w - new_w) / 2
            right = left + new_w
            img = img.crop((left, 0, right, h))
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) / 2
            bottom = top + new_h
            img = img.crop((0, top, w, bottom))
            
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')
        return byte_arr.getvalue()

def process_profile_photo_circular(image_source, size=(140, 140)):
        if image_source.startswith("http://") or image_source.startswith("https://"):
            resp = requests.get(image_source, timeout=5)
            img_data = resp.content
        else:
            if "base64," in image_source:
                image_source = image_source.split("base64,")[1]
            img_data = base64.b64decode(image_source)
            
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        # Center crop to square
        w, h = img.size
        crop_size = min(w, h)
        left = (w - crop_size)/2
        top = (h - crop_size)/2
        right = (w + crop_size)/2
        bottom = (h + crop_size)/2
        img = img.crop((left, top, right, bottom))
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        # Apply circular alpha mask
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        
        output = Image.new("RGBA", size, (255, 255, 255, 0))
        output.paste(img, (0, 0), mask)
        
        byte_arr = io.BytesIO()
        output.save(byte_arr, format='PNG')
        return byte_arr.getvalue()

def get_original_shape_mask(rect_width, rect_height):
    doc = fitz.open("tempalates/Progress 3rd to 5th 2026 updated.pdf")
    page = doc[1]
    paths = page.get_drawings()
    
    blob_path = None
    for p in paths:
        fill = p.get("fill")
        if fill and fill[0] > 0.5 and fill[1] < 0.5 and fill[2] < 0.5:
            blob_path = p
            break
            
    if not blob_path:
        raise Exception("Failed to locate Red Blob vector path on Page 2.")
        
    rect = blob_path["rect"]
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=rect.width, height=rect.height)
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
            
    out_page.draw_rect(out_page.rect, color=(0,0,0), fill=(0,0,0))
    shape.finish(color=(1,1,1), fill=(1,1,1))
    shape.commit()
    
    pix = out_page.get_pixmap(dpi=300)
    mask_bytes = pix.tobytes("png")
    mask_img = Image.open(io.BytesIO(mask_bytes)).convert("L")
    mask_img = mask_img.resize((int(rect_width), int(rect_height)), Image.Resampling.LANCZOS)
    return mask_img, rect

def process_profile_photo_original(image_source):
    mask_img, rect = get_original_shape_mask(205, 274)
    target_size = (int(rect.width), int(rect.height))
    
    if image_source.startswith("http://") or image_source.startswith("https://"):
        resp = requests.get(image_source, timeout=5)
        img_data = resp.content
    else:
        if "base64," in image_source:
            image_source = image_source.split("base64,")[1]
        img_data = base64.b64decode(image_source)
        
    img = Image.open(io.BytesIO(img_data)).convert("RGBA")
    
    w, h = img.size
    target_ratio = target_size[0] / target_size[1]
    img_ratio = w / h
    
    if img_ratio > target_ratio:
        new_w = int(target_ratio * h)
        left = (w - new_w) / 2
        right = left + new_w
        img = img.crop((left, 0, right, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) / 2
        bottom = top + new_h
        img = img.crop((0, top, w, bottom))
        
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    mask_img_resized = mask_img.resize(target_size, Image.Resampling.LANCZOS)
    
    output = Image.new("RGBA", target_size, (255, 255, 255, 0))
    output.paste(img, (0, 0), mask_img_resized)
    
    byte_arr = io.BytesIO()
    output.save(byte_arr, format='PNG')
    return byte_arr.getvalue(), rect

@st.cache_data(ttl=15)
def fetch_class_academic_data(class_id):
    from src.database.firebase_init import get_subjects
    sub_success, subjects = get_subjects(class_id)
    subject_map = {}
    if sub_success and subjects:
        import pandas as pd
        for sub in subjects:
            sub_name = sub.get("name")
            subject_map[sub_name] = {"t1": None, "t2": None}
            
            for term_key, dict_key in [("sheet_url_t1", "t1"), ("sheet_url_t2", "t2")]:
                url = sub.get(term_key, "")
                if url and "/d/" in url:
                    doc_id = url.split("/d/")[1].split("/")[0]
                    export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                    try:
                        raw_dict = pd.read_excel(export_url, sheet_name=None)
                        target_sheet = None
                        for k in raw_dict.keys():
                            if str(k).strip().lower() == "all grades":
                                target_sheet = k
                                break
                                
                        if target_sheet:
                            df = raw_dict[target_sheet]
                            header_idx = -1
                            for i, row in df.iterrows():
                                # In the new Google Sheet format (with merged headers), 
                                # the actual grades (C1.1, C1.2) are on a lower row than the "Name of Student" text.
                                # Let's search for a row that has C-codes in it so we get the correct horizontal layer.
                                has_grades = False
                                for val in row.values:
                                    val_str = str(val).strip().upper()
                                    if val_str in ["C1.1", "C1.2", "C1.3", "C2.1", "C2.2"]:
                                        has_grades = True
                                        break
                                
                                if has_grades:
                                    header_idx = i
                                    break
                                    
                            if header_idx != -1:
                                # Overwrite the first two columns of this grade row to be explicitly ROLL and NAME
                                # since they might be 'Unnamed: X' due to the merged cell above them.
                                new_cols = [str(c).upper().strip().replace(" ", "") for c in df.iloc[header_idx]]
                                if len(new_cols) >= 2:
                                    new_cols[0] = "ROLL"
                                    new_cols[1] = "NAME"
                                df.columns = new_cols
                                df = df[header_idx+1:].reset_index(drop=True)
                                # Fill nan to empty string
                                subject_map[sub_name][dict_key] = df.fillna("").astype(str)
                    except Exception as e:
                        st.error(f"Error fetching sheet for {sub_name} - {dict_key}: {e}. Ensure the Google Sheet link is viewable to 'Anyone with the link'.")
                        print(f"Error fetching sheet for {sub_name} - {dict_key}: {e}")
    return subject_map

def generate_report_card(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular", subject_data=None):
    """
    Injects student data into the predefined PDF template using PyMuPDF.
    Returns: BytesIO object containing the generated PDF
    """
    template_path = "tempalates/Progress 3rd to 5th 2026 updated.pdf"
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    # Open the existing PDF
    doc = fitz.open(template_path)
    
    # We are targeting Page 2 (index 1)
    page = doc[1] 
    
    # Define text insertion parameters
    color = hex_to_rgb(font_color)
    
    target_font_alias = "F0" if font_name_or_path.lower().endswith((".ttf", ".otf")) else font_name_or_path
    
    if font_name_or_path.lower().endswith((".ttf", ".otf")):
        try:
            for p_idx in range(len(doc)):
                doc[p_idx].insert_font(fontname=target_font_alias, fontfile=font_name_or_path)
        except Exception:
            target_font_alias = "helv"  # fallback if font is corrupt
    
    # Coordinates mapped from the template extraction
    
    # 1. Name of the Learner
    page.insert_text((175, 256.3), str(student_data.get('name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 2. APAAR ID/PEN
    page.insert_text((175, 292.1), str(student_data.get('apaar_id', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 3. Registration/Admission Number
    page.insert_text((175, 327.8), str(student_data.get('reg_number', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 4. Roll No 
    page.insert_text((175, 363.5), str(student_data.get('roll_number', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 5. Class & Section
    class_sec_str = f"{class_data.get('class_name', '')} - {class_data.get('section', '')}"
    page.insert_text((175, 399.2), class_sec_str, fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 6. Date of Birth
    page.insert_text((175, 435.0), str(student_data.get('dob', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 7. Class Teacher
    page.insert_text((175, 470.7), str(teacher_name), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 8. Mother's Name
    page.insert_text((175, 506.4), str(student_data.get('mother_name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 9. Father's Name
    page.insert_text((175, 542.1), str(student_data.get('father_name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 10. Profile Photo
    profile_photo_src = student_data.get('profile_photo', '')
    if profile_photo_src:
        try:
            if photo_shape == "Original":
                processed_img_bytes, target_rect = process_profile_photo_original(profile_photo_src)
                if processed_img_bytes and target_rect:
                    page.insert_image(target_rect, stream=processed_img_bytes)
            elif photo_shape == "Circular":
                circular_img_bytes = process_profile_photo_circular(profile_photo_src, size=(201, 201))
                if circular_img_bytes:
                    cx = (378.49 + 583.42) / 2
                    cy = (218.93 + 493.02) / 2
                    size = 201 
                    photo_rect = fitz.Rect(cx - size/2, cy - size/2, cx + size/2, cy + size/2)
                    page.insert_image(photo_rect, stream=circular_img_bytes)
            else: # Rectangular default
                processed_img_bytes = process_profile_photo_rectangular(profile_photo_src, target_size=(201, 274))
                if processed_img_bytes:
                    photo_rect = fitz.Rect(378.49 + 2, 218.93 + 2, 583.43 - 2, 493.02 - 2)
                    page.insert_image(photo_rect, stream=processed_img_bytes)
        except Exception as e:
            st.error(f"Failed to load or inject profile picture: {str(e)}")
            
    # --- ACADEMIC GRADES INJECTION (Pages 4 to 9) ---
    if subject_data:
        SUBJECT_ZONES = {
            "english": {"page": 3, "x_min": 595, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "hindi": {"page": 4, "x_min": 0, "x_max": 595, "y_min": 0, "y_max": 2000},
            "marathi": {"page": 4, "x_min": 595, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "mathematics": {"page": 5, "x_min": 0, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "environmental studies": {"page": 6, "x_min": 0, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "evs": {"page": 6, "x_min": 0, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "art": {"page": 7, "x_min": 0, "x_max": 2000, "y_min": 0, "y_max": 2000},
            "physical education": {"page": 8, "x_min": 0, "x_max": 595, "y_min": 0, "y_max": 420},
            "health and wellness": {"page": 8, "x_min": 0, "x_max": 595, "y_min": 420, "y_max": 2000},
            "health & wellness": {"page": 8, "x_min": 0, "x_max": 595, "y_min": 420, "y_max": 2000},
        }

        student_name_norm = str(student_data.get('name', '')).lower().strip().replace("  ", " ")
        student_roll_norm = str(student_data.get('roll_number', '')).strip()
        if student_roll_norm.endswith(".0"):
            student_roll_norm = student_roll_norm[:-2]
            
        def get_student_row(df):
            if df is None: return None
            for _, row in df.iterrows():
                sheet_roll = str(row.values[0]).strip()
                if sheet_roll.endswith(".0"): sheet_roll = sheet_roll[:-2]
                sheet_name = str(row.values[1]).lower().strip().replace("  ", " ")
                if (student_roll_norm and sheet_roll == student_roll_norm) or \
                   (student_name_norm and (student_name_norm in sheet_name or sheet_name in student_name_norm)):
                    return row
            return None

        for s_name, s_payload in subject_data.items():
            s_key = s_name.lower().strip()
            
            zone = None
            for z_key, z_val in SUBJECT_ZONES.items():
                if z_key in s_key or s_key in z_key:
                    zone = z_val
                    break
            
            if not zone:
                continue
                
            p = doc[zone["page"]]
            term1_df = s_payload.get("t1")
            term2_df = s_payload.get("t2")
            
            t1_row = get_student_row(term1_df)
            t2_row = get_student_row(term2_df)
            
            # Extract vector graphics to find true cell boundaries
            vector_y = set()
            for d in p.get_drawings():
                for item in d["items"]:
                    if item[0] == "l" and abs(item[1].y - item[2].y) < 2:
                        vector_y.add(round(item[1].y, 1))
                    elif item[0] == "re":
                        vector_y.add(round(item[1].y0, 1))
                        vector_y.add(round(item[1].y1, 1))
            vector_y = sorted(list(vector_y))
            
            all_codes = set()
            if t1_row is not None: all_codes.update(term1_df.columns)
            if t2_row is not None: all_codes.update(term2_df.columns)
            
            for cg_code in all_codes:
                cg_code = str(cg_code).strip()
                if not cg_code.startswith("C") or "." not in cg_code:
                    continue
                    
                rects = p.search_for(cg_code)
                for r in rects:
                    if zone["x_min"] <= r.x0 <= zone["x_max"] and zone["y_min"] <= r.y0 <= zone["y_max"]:
                        # Vertically center text based on the physical vector cell boundaries
                        cy = (r.y0 + r.y1) / 2.0
                        
                        above_lines = [y for y in vector_y if y < cy]
                        below_lines = [y for y in vector_y if y > cy]
                        
                        if above_lines and below_lines:
                            cell_top = max(above_lines)
                            cell_bottom = min(below_lines)
                            true_cy = (cell_top + cell_bottom) / 2.0
                        else:
                            true_cy = cy

                        y_pos = true_cy + (font_size * 0.33)  # adjust baseline 
                        
                        if r.x0 < 595:
                            t1_center = 469
                            t2_center = 528
                        else:
                            t1_center = 1056
                            t2_center = 1115
                            
                        if t1_row is not None and cg_code in term1_df.columns:
                            g1 = str(t1_row[cg_code]).strip()
                            if g1 and g1.lower() != 'nan':
                                offset_x = len(g1) * font_size * 0.28
                                p.insert_text((t1_center - offset_x, y_pos), g1, fontsize=font_size, color=color, fontname=target_font_alias)
                                
                        if t2_row is not None and cg_code in term2_df.columns:
                            g2 = str(t2_row[cg_code]).strip()
                            if g2 and g2.lower() != 'nan':
                                offset_x = len(g2) * font_size * 0.28
                                p.insert_text((t2_center - offset_x, y_pos), g2, fontsize=font_size, color=color, fontname=target_font_alias)
                        break
    
    # Save the modified PDF to an in-memory buffer
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    
    pdf_bytes.seek(0)
    return pdf_bytes

def get_pdf_preview(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular", subject_data=None):
    pdf_bytes = generate_report_card(student_data, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape, subject_data)
    doc = fitz.open("pdf", pdf_bytes)
    
    images = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=120)
        images.append(pix.tobytes("png"))
        
    doc.close()
    return images

def generate_class_bulk_report_merged(students_list, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular", progress_bar=None, status_text=None, subject_data=None):
    merged_pdf = fitz.open()
    total_stu = len(students_list)

    for idx, student in enumerate(students_list):
        if status_text:
            status_text.write(f"Generating PDF for Roll No: {student.get('roll_number')} - {student.get('name')} ...")
            
        pdf_bytes = generate_report_card(student, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape, subject_data)
        student_doc = fitz.open("pdf", pdf_bytes)
        merged_pdf.insert_pdf(student_doc)
        student_doc.close()
        
        if progress_bar:
            pct = int(((idx + 1) / total_stu) * 100)
            progress_bar.progress(pct, text=f"Completed {idx+1}/{total_stu} ({pct}%)")
            
    if status_text:
        status_text.write("Merging all generated PDFs into a single file...")
        
    final_bytes = io.BytesIO()
    merged_pdf.save(final_bytes)
    merged_pdf.close()
    final_bytes.seek(0)
    return final_bytes

def generate_class_bulk_report_zip(students_list, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular", progress_bar=None, status_text=None, subject_data=None):
    zip_buffer = io.BytesIO()
    total_stu = len(students_list)
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for idx, student in enumerate(students_list):
            if status_text:
                status_text.write(f"Generating PDF for Roll No: {student.get('roll_number')} - {student.get('name')} ...")
                
            pdf_bytes = generate_report_card(student, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape, subject_data)
            file_name = f"Report_Card_{student.get('roll_number')}_{student.get('name').replace(' ', '_')}.pdf"
            zip_file.writestr(file_name, pdf_bytes.getvalue())
            
            if progress_bar:
                pct = int(((idx + 1) / total_stu) * 100)
                progress_bar.progress(pct, text=f"Completed {idx+1}/{total_stu} ({pct}%)")
                
    if status_text:
        status_text.write("Packaging final PDF files into ZIP Archive...")
            
    zip_buffer.seek(0)
    return zip_buffer

def render_admin_results():
    st.header("📄 Result Generation")
    st.write("Generate official PDF report cards for students.")
    
    # 1. Fetch Classes
    c_success, classes_list = get_all_classes()
    
    if not c_success or not classes_list:
        st.warning("No classes found. Please create a class and add students first.")
        return
        
    class_options = {f"Class {c['class_name']} - Section {c['section']}": c['id'] for c in classes_list}
    class_map = {c['id']: c for c in classes_list}
    
    # Class Selection
    selected_class_label = st.selectbox("Select Target Class:", options=list(class_options.keys()))
    selected_class_id = class_options[selected_class_label]
    selected_class_data = class_map[selected_class_id]
    
    st.markdown("---")
    
    # 2. Fetch Students for Class
    s_success, students = get_students_by_class(selected_class_id)
    
    if s_success:
        if not students:
            st.info("No students enrolled in this class.")
        else:
            student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
            student_map = {s['id']: s for s in students}
            
            # Resolve Teacher Name
            t_success, users_list = get_all_users()
            teacher_name = selected_class_data.get('teacher_email', 'N/A')
            if t_success:
                for u in users_list:
                    if u['email'] == selected_class_data.get('teacher_email'):
                        teacher_name = u.get('name') if u.get('name') else u.get('email', teacher_name)
                        break

            res_tabs = st.tabs(["🧍 Individual Report", "📚 Bulk Class Report"])
            
            with res_tabs[0]:
                # Student Selection
                selected_student_label = st.selectbox("Select Student:", options=list(student_options.keys()))
                selected_student_data = student_map[student_options[selected_student_label]]

                # 3. Shadcn-style Data Preview Card
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                st.subheader("Student Data Preview")
                
                with st.container(border=True):
                    # Using columns for a sleek grid layout
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Name:** {selected_student_data.get('name', 'N/A')}")
                        st.markdown(f"**Roll Number:** {selected_student_data.get('roll_number', 'N/A')}")
                        st.markdown(f"**APAAR ID:** {selected_student_data.get('apaar_id', 'N/A')}")
                        st.markdown(f"**Registration No:** {selected_student_data.get('reg_number', 'N/A')}")
                        st.markdown(f"**Mother's Name:** {selected_student_data.get('mother_name', 'N/A')}")
                        
                    with col2:
                        st.markdown(f"**Class & Section:** Class {selected_class_data.get('class_name')} - {selected_class_data.get('section')}")
                        st.markdown(f"**Class Teacher:** {teacher_name}")
                        st.markdown(f"**Date of Birth:** {selected_student_data.get('dob', 'N/A')}")
                        st.markdown(f"**Email:** {selected_student_data.get('email', 'N/A')}")
                        st.markdown(f"**Father's Name:** {selected_student_data.get('father_name', 'N/A')}")

                st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                with st.expander("🔍 Show Full Extended Data Payload"):
                    from src.utils.excel_utils import flatten_student_for_export
                    flat_data = flatten_student_for_export(selected_student_data)
                    st.json(flat_data, expanded=False)

                # 4. Advanced PDF Style Settings
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                with st.expander("🎨 Advanced PDF Style Settings", expanded=True):
                    upl_fonts = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], accept_multiple_files=True, key="font_upl")
                    if upl_fonts:
                        if st.button("💾 Install Fonts Permanently"):
                            os.makedirs("fonts", exist_ok=True)
                            for upl_font in upl_fonts:
                                font_path = os.path.join("fonts", upl_font.name)
                                with open(font_path, "wb") as f:
                                    f.write(upl_font.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {len(upl_fonts)} font(s)!")
                            st.rerun()
                                
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    
                    font_family_map = get_available_fonts()
                    
                    sel_family = c1.selectbox("Font Family & Style", list(font_family_map.keys()))
                    sel_color = c2.color_picker("Text Color", "#000000")
                    sel_size = c3.number_input("Font Size", min_value=6, max_value=24, value=11)
                    
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    sel_shape = st.selectbox("Profile Photo Shape", ["Rectangular", "Circular", "Original"], help="Rectangular matches background box. Circular makes an ID-card circle. Original extracts organic PDF background shape exactly.")
                    
                    target_fontname = font_family_map[sel_family]
                    
                    if st.button("👁️ Generate Live Preview"):
                        with st.spinner("Fetching Academic Grades from Google Sheets & Rendering Full Preview..."):
                            pre_data = fetch_class_academic_data(selected_class_id)
                            preview_imgs = get_pdf_preview(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape, pre_data)
                            for idx, img_bytes in enumerate(preview_imgs):
                                st.image(img_bytes, caption=f"Page {idx+1} Preview", use_container_width=True)

                # 5. Generation & Download Action
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                if st.button("⚙️ Generate Final Report Card", type="primary"):
                    with st.status("Generating Report Card...", expanded=True) as status:
                        progress_bar = status.progress(0, text="Starting Generation Workflow...")
                        st.write("Locating Template `Progress 3rd to 5th 2026 updated.pdf`...")
                        progress_bar.progress(15, text="Locating Template...")
                        
                        st.write("Fetching Academic Data from Google Sheets...")
                        sub_data = fetch_class_academic_data(selected_class_id)
                        progress_bar.progress(40, text="Academic Data Fetched.")
                        
                        with st.container(border=True):
                            st.write("🛠️ **DEBUG: Fetched Sheet Data (Check Columns)**")
                            if not sub_data:
                                st.warning("No subject links provided or data failed to fetch.")
                            else:
                                for sub_k, sub_v in sub_data.items():
                                    t1_df = sub_v.get("t1")
                                    t2_df = sub_v.get("t2")
                                    t1_cols = t1_df.columns.tolist() if getattr(t1_df, "columns", None) is not None else "None"
                                    t2_cols = t2_df.columns.tolist() if getattr(t2_df, "columns", None) is not None else "None"
                                    st.write(f"**{sub_k}**:")
                                    st.write(f"- Term 1 Columns: {t1_cols}")
                                    st.write(f"- Term 2 Columns: {t2_cols}")
                        
                        st.write("Extracting Student Profile Data...")
                        progress_bar.progress(55, text="Profile Data Extracted.")
                        
                        st.write("Mapping coordinates to Page 3 & Academic Pages 5-10...")
                        progress_bar.progress(70, text="Injecting Data via PyMuPDF...")
                        
                        try:
                            pdf_buffer = generate_report_card(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape, sub_data)
                            st.write("Injecting Data Streams...")
                            progress_bar.progress(90, text="Finalizing PDF Document...")
                            
                            st.write("Finalizing PDF Document...")
                            progress_bar.progress(100, text="Completed!")
                            status.update(label="Report Card Generated Successfully!", state="complete", expanded=False)
                            
                            file_name = f"Report_Card_{selected_student_data.get('roll_number')}_{selected_student_data.get('name').replace(' ', '_')}.pdf"
                            
                            # Provide the download button immediately
                            st.download_button(
                                label="📥 Download PDF Report Card",
                                data=pdf_buffer,
                                file_name=file_name,
                                mime="application/pdf",
                                type="secondary"
                            )
                            st.balloons()
                            
                            # Render Final PDF in Browser
                            st.subheader("Final Generated PDF Preview")
                            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                        except Exception as e:
                            status.update(label="Failed to generate report card.", state="error")
                            st.error(f"Error compiling PDF: {e}")
                            
            with res_tabs[1]:
                st.subheader(f"Generate Reports for all {len(students)} students in Class {selected_class_data.get('class_name')}-{selected_class_data.get('section')}")
                st.write("This will merge all report cards into a single downloadable PDF document.")
                
                # Shared Style Settings
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                with st.expander("🎨 Bulk PDF Style Settings", expanded=False):
                    upl_fonts_b = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], accept_multiple_files=True, key="font_upl_b")
                    if upl_fonts_b:
                        if st.button("💾 Install Fonts Permanently", key="inst_btn_b"):
                            os.makedirs("fonts", exist_ok=True)
                            for upl_font_b in upl_fonts_b:
                                font_path = os.path.join("fonts", upl_font_b.name)
                                with open(font_path, "wb") as f:
                                    f.write(upl_font_b.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {len(upl_fonts_b)} font(s)!")
                            st.rerun()
                                
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    font_family_map_b = get_available_fonts()
                    sel_family_b = c1.selectbox("Font Family & Style", list(font_family_map_b.keys()), key="bulk_font")
                    sel_color_b = c2.color_picker("Text Color", "#000000", key="bulk_color")
                    sel_size_b = c3.number_input("Font Size", min_value=6, max_value=24, value=11, key="bulk_size")
                    
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    sel_shape_b = st.selectbox("Profile Photo Shape", ["Rectangular", "Circular", "Original"], key="bulk_shape")
                    
                    target_fontname_b = font_family_map_b[sel_family_b]

                st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                export_format = st.radio("Bulk Export Format", options=["Merged PDF (Single File)", "ZIP Archive (Individual PDFs)"], horizontal=True)

                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                if st.button("⚙️ Generate Bulk Report Cards", type="primary"):
                    with st.status("Generating Bulk Report Cards...", expanded=True) as status:
                        try:
                            st.write(f"Processing {len(students)} students...")
                            st.write("Fetching Academic Data from Google Sheets...")
                            sub_data = fetch_class_academic_data(selected_class_id)
                            
                            is_zip = "ZIP Archive" in export_format
                            if is_zip:
                                progress_bar = status.progress(0, text="Starting ZIP generation...")
                                file_buffer = generate_class_bulk_report_zip(students, selected_class_data, teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b, progress_bar=progress_bar, status_text=status, subject_data=sub_data)
                                file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.zip"
                                mime_type = "application/zip"
                            else:
                                progress_bar = status.progress(0, text="Starting Merged PDF generation...")
                                file_buffer = generate_class_bulk_report_merged(students, selected_class_data, teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b, progress_bar=progress_bar, status_text=status, subject_data=sub_data)
                                file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.pdf"
                                mime_type = "application/pdf"
                                
                            status.update(label="Bulk Report Generated Successfully!", state="complete", expanded=False)
                            
                            st.download_button(
                                label=f"📥 Download {is_zip and 'ZIP Archive' or 'Bulk PDF'}",
                                data=file_buffer,
                                file_name=file_name,
                                mime=mime_type,
                                type="secondary"
                            )
                            st.balloons()
                        except Exception as e:
                            status.update(label="Failed to generate bulk reports.", state="error")
                            st.error(f"Error compiling PDF: {e}")
                        
    else:
        st.error(f"Failed to load students: {students}")
