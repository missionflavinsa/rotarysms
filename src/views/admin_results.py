import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import os
from src.database.firebase_init import get_all_classes, get_students_by_class, get_all_users

def generate_report_card(student_data, class_data, teacher_name):
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
    font_size = 11
    color = (0, 0, 0) # Black
    
    # Coordinates mapped from the template extraction
    # Format: (x, y) starting point for text
    
    # 1. Name of the Learner
    page.insert_text((180, 255), str(student_data.get('name', 'N/A')), fontsize=font_size, color=color)
    
    # 2. APAAR ID/PEN
    page.insert_text((150, 290), str(student_data.get('apaar_id', 'N/A')), fontsize=font_size, color=color)
    
    # 3. Registration/Admission Number
    page.insert_text((250, 325), str(student_data.get('reg_number', 'N/A')), fontsize=font_size, color=color)
    
    # 4. Roll No 
    page.insert_text((100, 360), str(student_data.get('roll_number', 'N/A')), fontsize=font_size, color=color)
    
    # 5. Class & Section
    class_sec_str = f"{class_data.get('class_name', '')} - {class_data.get('section', '')}"
    page.insert_text((150, 397), class_sec_str, fontsize=font_size, color=color)
    
    # 6. Date of Birth
    page.insert_text((130, 432), str(student_data.get('dob', 'N/A')), fontsize=font_size, color=color)
    
    # 7. Class Teacher
    page.insert_text((140, 468), str(teacher_name), fontsize=font_size, color=color)
    
    # Save the modified PDF to an in-memory buffer
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    
    pdf_bytes.seek(0)
    return pdf_bytes

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
            
            # Student Selection
            selected_student_label = st.selectbox("Select Student:", options=list(student_options.keys()))
            selected_student_data = student_map[student_options[selected_student_label]]
            
            # Resolve Teacher Name
            t_success, users_list = get_all_users()
            teacher_name = selected_class_data.get('teacher_email', 'N/A')
            if t_success:
                for u in users_list:
                    if u['email'] == selected_class_data.get('teacher_email'):
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
                    
                with col2:
                    st.markdown(f"**Class & Section:** Class {selected_class_data.get('class_name')} - {selected_class_data.get('section')}")
                    st.markdown(f"**Class Teacher:** {teacher_name}")
                    st.markdown(f"**Date of Birth:** {selected_student_data.get('dob', 'N/A')}")
                    st.markdown(f"**Email:** {selected_student_data.get('email', 'N/A')}")

            # 4. Generation & Download Action
            st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            
            if st.button("⚙️ Generate Report Card", type="primary"):
                with st.status("Generating Report Card...", expanded=True) as status:
                    st.write("Locating Template `Progress 3rd to 5th 2026.pdf`...")
                    st.write("Extracting Student Profile Data...")
                    st.write("Mapping coordinates to Page 3...")
                    
                    try:
                        pdf_buffer = generate_report_card(selected_student_data, selected_class_data, teacher_name)
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
                        
    else:
        st.error(f"Failed to load students: {students}")
