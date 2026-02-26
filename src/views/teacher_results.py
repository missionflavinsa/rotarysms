import streamlit as st
import pandas as pd
import os
from src.views.admin_results import get_available_fonts, get_pdf_preview, generate_report_card, generate_class_bulk_report_merged, generate_class_bulk_report_zip, fetch_class_academic_data
from src.database.firebase_init import get_classes_for_teacher, get_students_by_class, get_all_users

def render_teacher_results(teacher_email):
    st.header("📄 Result Generation")
    st.write("Generate official PDF report cards for students.")
    
    # 1. Fetch Classes assigned to this teacher
    c_success, classes_list = get_classes_for_teacher(teacher_email)
    
    if not c_success or not classes_list:
        st.warning("No classes are assigned to you yet. You cannot generate report cards.")
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
            
            res_tabs = st.tabs(["🧍 Individual Report", "📚 Bulk Class Report"])
            
            with res_tabs[0]:
                # Student Selection
                selected_student_label = st.selectbox("Select Student:", options=list(student_options.keys()))
                selected_student_data = student_map[student_options[selected_student_label]]
                
                # Resolve Teacher Name (themselves, or if somehow different logic applies)
                t_success, users_list = get_all_users()
                teacher_name = teacher_email
                if t_success:
                    for u in users_list:
                        if u['email'] == teacher_email:
                            teacher_name = u.get('name') if u.get('name') else u.get('email', teacher_name)
                            break

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
                    upl_fonts_t1 = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], accept_multiple_files=True, key=f"font_upl_t1_{selected_student_data.get('id')}")
                    if upl_fonts_t1:
                        if st.button("💾 Install Fonts Permanently", key=f"inst_btn_t1_{selected_student_data.get('id')}"):
                            os.makedirs("fonts", exist_ok=True)
                            for upl_font_t1 in upl_fonts_t1:
                                font_path = os.path.join("fonts", upl_font_t1.name)
                                with open(font_path, "wb") as f:
                                    f.write(upl_font_t1.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {len(upl_fonts_t1)} font(s)!")
                            st.rerun()
                                
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    
                    font_family_map = get_available_fonts()
                    
                    sel_family = c1.selectbox("Font Family & Style", list(font_family_map.keys()), key=f"font_{selected_student_data.get('id')}")
                    sel_color = c2.color_picker("Text Color", "#000000", key=f"color_{selected_student_data.get('id')}")
                    sel_size = c3.number_input("Font Size", min_value=6, max_value=24, value=11, key=f"size_{selected_student_data.get('id')}")
                    
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    sel_shape = st.selectbox("Profile Photo Shape", ["Rectangular", "Circular", "Original"], help="Rectangular matches background box. Circular makes an ID-card circle. Original extracts organic PDF background shape exactly.", key=f"shape_{selected_student_data.get('id')}")
                    
                    target_fontname = font_family_map[sel_family]
                    
                    if st.button("👁️ Generate Live Preview", key=f"prev_gen_{selected_student_data.get('id')}"):
                        with st.spinner("Fetching Academic Grades from Google Sheets & Rendering Full Preview..."):
                            pre_data = fetch_class_academic_data(selected_class_id)
                            preview_imgs = get_pdf_preview(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape, pre_data)
                            for idx, img_bytes in enumerate(preview_imgs):
                                st.image(img_bytes, caption=f"Page {idx+1} Preview", use_container_width=True)

                # 5. Generation & Download Action
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                if st.button("⚙️ Generate Final Report Card", type="primary", key=f"btn_gen_{selected_student_data.get('id')}"):
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
                            # Re-use the generation logic from admin results
                            pdf_buffer = generate_report_card(selected_student_data, selected_class_data, teacher_name, target_fontname, sel_size, sel_color, sel_shape, sub_data)
                            st.write("Injecting Data Streams...")
                            progress_bar.progress(90, text="Finalizing PDF Document...")
                            
                            import base64
                            
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
                                type="secondary",
                                key=f"dl_btn_{selected_student_data.get('id')}"
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
                    upl_fonts_t2 = st.file_uploader("Upload & Install Custom Font (.ttf / .otf)", type=["ttf", "otf"], accept_multiple_files=True, key="font_upl_t2_bulk")
                    if upl_fonts_t2:
                        if st.button("💾 Install Fonts Permanently", key="inst_btn_t2_bulk"):
                            os.makedirs("fonts", exist_ok=True)
                            for upl_font_t2 in upl_fonts_t2:
                                font_path = os.path.join("fonts", upl_font_t2.name)
                                with open(font_path, "wb") as f:
                                    f.write(upl_font_t2.getvalue())
                            get_available_fonts.clear()
                            st.success(f"Successfully installed {len(upl_fonts_t2)} font(s)!")
                            st.rerun()
                                
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    font_family_map_b = get_available_fonts()
                    sel_family_b = c1.selectbox("Font Family & Style", list(font_family_map_b.keys()), key="bulk_font_t")
                    sel_color_b = c2.color_picker("Text Color", "#000000", key="bulk_color_t")
                    sel_size_b = c3.number_input("Font Size", min_value=6, max_value=24, value=11, key="bulk_size_t")
                    
                    st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    sel_shape_b = st.selectbox("Profile Photo Shape", ["Rectangular", "Circular", "Original"], key="bulk_shape_t")
                    
                    target_fontname_b = font_family_map_b[sel_family_b]

                st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                export_format = st.radio("Bulk Export Format", options=["Merged PDF (Single File)", "ZIP Archive (Individual PDFs)"], horizontal=True)

                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                if st.button("⚙️ Generate Bulk Report Cards", type="primary", key="btn_gen_bulk_t"):
                    with st.status("Generating Bulk Report Cards...", expanded=True) as status:
                        try:
                            st.write(f"Processing {len(students)} students...")
                            st.write("Fetching Academic Data from Google Sheets...")
                            sub_data = fetch_class_academic_data(selected_class_id)
                            # we need teacher name
                            t_success, users_list = get_all_users()
                            bulk_teacher_name = teacher_email
                            if t_success:
                                for u in users_list:
                                    if u['email'] == teacher_email:
                                        bulk_teacher_name = u.get('name') if u.get('name') else u.get('email', bulk_teacher_name)
                                        break
                            is_zip = "ZIP Archive" in export_format
                            if is_zip:
                                progress_bar = status.progress(0, text="Starting ZIP generation...")
                                file_buffer = generate_class_bulk_report_zip(students, selected_class_data, bulk_teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b, progress_bar=progress_bar, status_text=status, subject_data=sub_data)
                                file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.zip"
                                mime_type = "application/zip"
                            else:
                                progress_bar = status.progress(0, text="Starting Merged PDF generation...")
                                file_buffer = generate_class_bulk_report_merged(students, selected_class_data, bulk_teacher_name, target_fontname_b, sel_size_b, sel_color_b, sel_shape_b, progress_bar=progress_bar, status_text=status, subject_data=sub_data)
                                file_name = f"Bulk_Reports_Class_{selected_class_data.get('class_name')}_{selected_class_data.get('section')}.pdf"
                                mime_type = "application/pdf"
                                
                            status.update(label="Bulk Report Generated Successfully!", state="complete", expanded=False)
                            
                            st.download_button(
                                label=f"📥 Download {is_zip and 'ZIP Archive' or 'Bulk PDF'}",
                                data=file_buffer,
                                file_name=file_name,
                                mime=mime_type,
                                type="secondary",
                                key="btn_dl_bulk_t"
                            )
                            st.balloons()
                        except Exception as e:
                            status.update(label="Failed to generate bulk reports.", state="error")
                            st.error(f"Error compiling PDF: {e}")
                        
    else:
        st.error(f"Failed to load students: {students}")
