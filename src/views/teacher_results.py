import streamlit as st
import pandas as pd
from src.views.admin_results import generate_report_card
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
                    
                with col2:
                    st.markdown(f"**Class & Section:** Class {selected_class_data.get('class_name')} - {selected_class_data.get('section')}")
                    st.markdown(f"**Class Teacher:** {teacher_name}")
                    st.markdown(f"**Date of Birth:** {selected_student_data.get('dob', 'N/A')}")
                    st.markdown(f"**Email:** {selected_student_data.get('email', 'N/A')}")

            # 4. Generation & Download Action
            st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            
            if st.button("⚙️ Generate Report Card", type="primary", key=f"btn_gen_{selected_student_data.get('id')}"):
                with st.status("Generating Report Card...", expanded=True) as status:
                    st.write("Locating Template `Progress 3rd to 5th 2026.pdf`...")
                    st.write("Extracting Student Profile Data...")
                    st.write("Mapping coordinates to Page 3...")
                    
                    try:
                        # Re-use the generation logic from admin results
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
