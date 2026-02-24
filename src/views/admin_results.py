import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import os
import glob
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
    
    # Load system TTFs safely
    for path in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        name = os.path.basename(path).replace(".ttf", "").replace("-", " ")
        fonts[f"{name} (System)"] = path
        
    return fonts

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

def generate_report_card(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000"):
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
    # Format: (x, y) starting point for text
    
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
    
    # Save the modified PDF to an in-memory buffer
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    
    pdf_bytes.seek(0)
    return pdf_bytes

def get_pdf_preview(student_data, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000"):
    pdf_bytes = generate_report_card(student_data, class_data, teacher_name, font_name_or_path, font_size, font_color)
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[2] # we inserted into page 3
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes

def generate_class_bulk_report(students_list, class_data, teacher_name, font_name_or_path="helv", font_size=11, font_color="#000000"):
    merged_pdf = fitz.open()

    for student in students_list:
        pdf_bytes = generate_report_card(student, class_data, teacher_name, font_name_or_path, font_size, font_color)
        student_doc = fitz.open("pdf", pdf_bytes)
        merged_pdf.insert_pdf(student_doc)
        student_doc.close()
        
    final_bytes = io.BytesIO()
    merged_pdf.save(final_bytes)
    merged_pdf.close()
    final_bytes.seek(0)
    return final_bytes

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

                # 4. Advanced PDF Style Settings
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                with st.expander("🎨 Advanced PDF Style Settings", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    
                    font_family_map = get_available_fonts()
                    
                    sel_family = c1.selectbox("Font Family & Style", list(font_family_map.keys()))
                    sel_color = c2.color_picker("Text Color", "#000000")
                    sel_size = c3.number_input("Font Size", min_value=6, max_value=24, value=11)
                    
                    target_fontname = font_family_map[sel_family]
                    
                    if st.button("👁️ Generate Live Preview"):
                        with st.spinner("Rendering PDF Preview..."):
                            preview_img = get_pdf_preview(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color)
                            st.image(preview_img, caption="Page 3 Live Preview", use_container_width=True)

                # 5. Generation & Download Action
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                if st.button("⚙️ Generate Final Report Card", type="primary"):
                    with st.status("Generating Report Card...", expanded=True) as status:
                        st.write("Locating Template `Progress 3rd to 5th 2026.pdf`...")
                        st.write("Extracting Student Profile Data...")
                        st.write("Mapping coordinates to Page 3...")
                        
                        try:
                            pdf_buffer = generate_report_card(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color)
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
                    c1, c2, c3 = st.columns(3)
                    font_family_map_b = get_available_fonts()
                    sel_family_b = c1.selectbox("Font Family & Style", list(font_family_map_b.keys()), key="bulk_font")
                    sel_color_b = c2.color_picker("Text Color", "#000000", key="bulk_color")
                    sel_size_b = c3.number_input("Font Size", min_value=6, max_value=24, value=11, key="bulk_size")
                    target_fontname_b = font_family_map_b[sel_family_b]

                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                if st.button("⚙️ Generate Bulk Report Cards", type="primary"):
                    with st.status("Generating Bulk Report Cards...", expanded=True) as status:
                        try:
                            st.write(f"Processing {len(students)} students...")
                            pdf_buffer = generate_class_bulk_report(students, selected_class_data, teacher_name, target_fontname_b, sel_size_b, sel_color_b)
                            status.update(label="Bulk Report Generated Successfully!", state="complete", expanded=False)
                            
                            file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.pdf"
                            
                            st.download_button(
                                label="📥 Download Bulk PDF Report",
                                data=pdf_buffer,
                                file_name=file_name,
                                mime="application/pdf",
                                type="secondary"
                            )
                            st.balloons()
                        except Exception as e:
                            status.update(label="Failed to generate bulk reports.", state="error")
                            st.error(f"Error compiling PDF: {e}")
                        
    else:
        st.error(f"Failed to load students: {students}")
