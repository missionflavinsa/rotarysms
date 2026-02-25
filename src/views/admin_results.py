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
    for path in glob.glob("fonts/*.ttf") + glob.glob("fonts/*.otf"):
        name = os.path.basename(path).replace(".ttf", "").replace(".otf", "").replace("-", " ")
        fonts[f"{name} (Custom)"] = path
        
    # Load system TTFs safely
    for path in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        name = os.path.basename(path).replace(".ttf", "").replace("-", " ")
        fonts[f"{name} (System)"] = path
        
    return fonts

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

def process_profile_photo_rectangular(image_source, target_size=(201, 270)):
    try:
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
    except Exception as e:
        print(f"Error processing rectangular image for PDF: {e}")
        return None

def process_profile_photo_circular(image_source, size=(140, 140)):
    try:
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
    except Exception as e:
        print(f"Error processing circular image for PDF: {e}")
        return None

def get_original_shape_mask(rect_width, rect_height):
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
        return None
        
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
    try:
        mask_res = get_original_shape_mask(205, 274)
        if not mask_res:
            return None, None
        mask_img, rect = mask_res
        
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
    except Exception as e:
        print(f"Error processing original image for PDF: {e}")
        return None, None

def generate_report_card(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular"):
    """
    Injects student data into the predefined PDF template using PyMuPDF.
    Returns: BytesIO object containing the generated PDF
    """
    template_path = "tempalates/Progress 3rd to 5th 2026.pdf"
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    # Open the existing PDF
    doc = fitz.open(template_path)
    
    # We are targeting Page 3 (index 2)
    page = doc[2] 
    
    # Define text insertion parameters
    color = hex_to_rgb(font_color)
    
    target_font_alias = "F0" if font_name_or_path.endswith(".ttf") else font_name_or_path
    
    if font_name_or_path.endswith(".ttf"):
        try:
            page.insert_font(fontname=target_font_alias, fontfile=font_name_or_path)
        except Exception:
            target_font_alias = "helv"  # fallback if font is corrupt
    
    # Coordinates mapped from the template extraction
    
    # 1. Name of the Learner
    page.insert_text((180, 255), str(student_data.get('name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 2. APAAR ID/PEN
    page.insert_text((150, 290), str(student_data.get('apaar_id', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 3. Registration/Admission Number
    page.insert_text((250, 325), str(student_data.get('reg_number', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 4. Roll No 
    page.insert_text((100, 360), str(student_data.get('roll_number', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 5. Class & Section
    class_sec_str = f"{class_data.get('class_name', '')} - {class_data.get('section', '')}"
    page.insert_text((150, 397), class_sec_str, fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 6. Date of Birth
    page.insert_text((130, 432), str(student_data.get('dob', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 7. Class Teacher
    page.insert_text((140, 468), str(teacher_name), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 8. Mother's Name
    page.insert_text((150, 506), str(student_data.get('mother_name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
    # 9. Father's Name
    page.insert_text((150, 542), str(student_data.get('father_name', 'N/A')), fontsize=font_size, color=color, fontname=target_font_alias)
    
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
                    cy = (262.49 + 536.57) / 2
                    size = 201 
                    photo_rect = fitz.Rect(cx - size/2, cy - size/2, cx + size/2, cy + size/2)
                    page.insert_image(photo_rect, stream=circular_img_bytes)
            else: # Rectangular default
                processed_img_bytes = process_profile_photo_rectangular(profile_photo_src, target_size=(201, 270))
                if processed_img_bytes:
                    photo_rect = fitz.Rect(378.49 + 2, 262.50 + 2, 583.43 - 2, 536.58 - 2)
                    page.insert_image(photo_rect, stream=processed_img_bytes)
        except Exception:
            pass
    
    # Save the modified PDF to an in-memory buffer
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    
    pdf_bytes.seek(0)
    return pdf_bytes

def get_pdf_preview(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular"):
    pdf_bytes = generate_report_card(student_data, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape)
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[2] # we inserted into page 3
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes

def generate_class_bulk_report_merged(students_list, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular"):
    merged_pdf = fitz.open()

    for student in students_list:
        pdf_bytes = generate_report_card(student, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape)
        student_doc = fitz.open("pdf", pdf_bytes)
        merged_pdf.insert_pdf(student_doc)
        student_doc.close()
        
    final_bytes = io.BytesIO()
    merged_pdf.save(final_bytes)
    merged_pdf.close()
    final_bytes.seek(0)
    return final_bytes

def generate_class_bulk_report_zip(students_list, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000", photo_shape="Rectangular"):
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for student in students_list:
            pdf_bytes = generate_report_card(student, class_data, teacher_name, font_name_or_path, font_size, font_color, photo_shape)
            file_name = f"Report_Card_{student.get('roll_number')}_{student.get('name').replace(' ', '_')}.pdf"
            zip_file.writestr(file_name, pdf_bytes.getvalue())
            
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
                    upl_font = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], key="font_upl")
                    if upl_font:
                        if st.button("💾 Install Font Permanently"):
                            os.makedirs("fonts", exist_ok=True)
                            font_path = os.path.join("fonts", upl_font.name)
                            with open(font_path, "wb") as f:
                                f.write(upl_font.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {upl_font.name}!")
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
                        with st.spinner("Rendering PDF Preview..."):
                            preview_img = get_pdf_preview(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape)
                            st.image(preview_img, caption="Page 3 Live Preview", use_container_width=True)

                # 5. Generation & Download Action
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                if st.button("⚙️ Generate Final Report Card", type="primary"):
                    with st.status("Generating Report Card...", expanded=True) as status:
                        st.write("Locating Template `Progress 3rd to 5th 2026.pdf`...")
                        st.write("Extracting Student Profile Data...")
                        st.write("Mapping coordinates to Page 3...")
                        
                        try:
                            pdf_buffer = generate_report_card(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape)
                            st.write("Injecting Data Streams...")
                            st.write("Finalizing PDF Document...")
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
                            
                        except Exception as e:
                            status.update(label="Failed to generate report card.", state="error")
                            st.error(f"Error compiling PDF: {e}")
                            
            with res_tabs[1]:
                st.subheader(f"Generate Reports for all {len(students)} students in Class {selected_class_data.get('class_name')}-{selected_class_data.get('section')}")
                st.write("This will merge all report cards into a single downloadable PDF document.")
                
                # Shared Style Settings
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                with st.expander("🎨 Bulk PDF Style Settings", expanded=False):
                    upl_font_b = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], key="font_upl_b")
                    if upl_font_b:
                        if st.button("💾 Install Font Permanently", key="inst_btn_b"):
                            os.makedirs("fonts", exist_ok=True)
                            font_path = os.path.join("fonts", upl_font_b.name)
                            with open(font_path, "wb") as f:
                                f.write(upl_font_b.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {upl_font_b.name}!")
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
                            
                            is_zip = "ZIP Archive" in export_format
                            if is_zip:
                                file_buffer = generate_class_bulk_report_zip(students, selected_class_data, teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b)
                                file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.zip"
                                mime_type = "application/zip"
                            else:
                                file_buffer = generate_class_bulk_report_merged(students, selected_class_data, teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b)
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
