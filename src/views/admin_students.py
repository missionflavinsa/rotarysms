import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from src.database.firebase_init import (get_all_classes, add_student, bulk_import_students, 
                                        get_students_by_class, update_student, delete_student, get_all_users)

def render_students():
    st.header("👨‍🎓 Student Management")
    st.write("Manage student records and class assignments.")
    
    c_success, classes_list = get_all_classes()
    t_success, users_list = get_all_users()
    
    # Create mapping of email to Name (Email)
    teacher_name_map = {}
    if t_success and users_list:
        for u in users_list:
            teacher_name_map[u['email']] = f"{u.get('name', '')} ({u['email']})" if u.get('name') else u['email']
    
    if not c_success or not classes_list:
        st.warning("You must create at least one class before adding students.")
    else:
        class_options = {f"Class {c['class_name']} - Section {c['section']}": c['id'] for c in classes_list}
        class_map = {c['id']: c for c in classes_list}
        selected_class_label = st.selectbox("Select Target Class:", options=list(class_options.keys()))
        selected_class_id = class_options[selected_class_label]
        
        st.markdown("---")
        st_tab1, st_tab2, st_tab3 = st.tabs(["📋 View & Edit", "➕ Add Individual", "📁 Bulk Import"])
        
        with st_tab1:
            s_success, students = get_students_by_class(selected_class_id)
            if s_success:
                if not students:
                    st.info("No students enrolled in this class.")
                else:
                    df_students = pd.DataFrame(students)
                    display_cols = ['roll_number', 'name']
                    if 'reg_number' in df_students.columns: display_cols.append('reg_number')
                    if 'apaar_id' in df_students.columns: display_cols.append('apaar_id')
                    if 'dob' in df_students.columns: display_cols.append('dob')
                    if 'email' in df_students.columns: display_cols.append('email')
                    st.dataframe(df_students[display_cols], hide_index=True, use_container_width=True)
                    
                    student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
                    student_map = {s['id']: s for s in students}
                    
                    st.write("**Manage Student Data**")
                    with st.container(border=True):
                        selected_student_label = st.selectbox(f"Select Student", options=list(student_options.keys()), key=f"admin_sel_stu_{selected_class_id}")
                        selected_student_id = student_options[selected_student_label]
                        selected_student_data = student_map[selected_student_id]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.form(f"admin_update_stu_form"):
                                u_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"])
                                u_name = st.text_input("Name of the Learner", value=selected_student_data.get('name', ''))
                                u_apaar = st.text_input("APAAR ID/PEN", value=selected_student_data.get('apaar_id', ''))
                                u_reg = st.text_input("Registration/Admission Number", value=selected_student_data.get('reg_number', ''))
                                u_roll = st.text_input("Roll Number", value=selected_student_data.get('roll_number', ''))
                                
                                dob_str = selected_student_data.get('dob', '')
                                try:
                                    def_dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
                                except:
                                    def_dob = None
                                u_dob = st.date_input("Date of Birth", value=def_dob)
                                u_email = st.text_input("Email", value=selected_student_data.get('email', ''))
                                
                                upd_btn = st.form_submit_button("Update Student")
                                if upd_btn:
                                    if not u_roll or not u_name:
                                        st.error("Roll Number and Name are required.")
                                    else:
                                        with st.spinner("Updating student..."):
                                            photo_b64 = selected_student_data.get('profile_photo', '')
                                            if u_photo:
                                                photo_b64 = base64.b64encode(u_photo.getvalue()).decode()
                                                                                            
                                            up_success, up_res = update_student(
                                                selected_student_id, roll_number=u_roll, name=u_name, 
                                                apaar_id=u_apaar, reg_number=u_reg, dob=str(u_dob) if u_dob else "", 
                                                profile_photo=photo_b64, email=u_email
                                            )
                                        if up_success:
                                            st.success("Successfully updated student.")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update: {up_res}")
                        with col2:
                            with st.form(f"admin_delete_stu_form"):
                                st.write('<div style="height: 38px;"></div>', unsafe_allow_html=True)
                                st.warning("This action cannot be undone.")
                                del_btn = st.form_submit_button("Delete Student", type="primary")
                                
                                if del_btn:
                                    with st.spinner("Deleting student..."):
                                        del_success, del_res = delete_student(selected_student_id)
                                    if del_success:
                                        st.success("Successfully deleted student.")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {del_res}")
            else:
                st.error(f"Failed to load students: {students}")

        with st_tab2:
            with st.form("add_individual_student_form"):
                n_photo = st.file_uploader("1. Profile Photo", type=["png", "jpg", "jpeg"])
                
                n_name = st.text_input("2. Name of the Learner")
                n_apaar = st.text_input("3. APAAR ID/PEN")
                n_reg = st.text_input("4. Registration/Admission Number")
                n_roll = st.text_input("5. Roll Number")
                
                # Requested Dropdowns
                n_class_id = st.selectbox("6. Class & Section", options=list(class_options.values()), format_func=lambda x: [k for k,v in class_options.items() if v == x][0], index=list(class_options.values()).index(selected_class_id))
                
                n_dob = st.date_input("7. Date of Birth", value=None)
                
                # Fetch teacher for visual display from the selected class mapping (if available)
                target_cls_data = class_map.get(n_class_id, {})
                assigned_teacher = target_cls_data.get('teacher_email', '')
                
                # Use the map to show Name (Email)
                default_t_idx = list(teacher_name_map.keys()).index(assigned_teacher) if assigned_teacher in teacher_name_map else 0
                n_teacher_label = st.selectbox("8. Class Teacher", options=list(teacher_name_map.values()), index=default_t_idx)
                
                # Reverse lookup the email from the selected label if needed, though we don't strictly save teacher to student
                # n_teacher = [k for k, v in teacher_name_map.items() if v == n_teacher_label][0]
                
                n_email = st.text_input("Email (Optional)")
                
                submit_student = st.form_submit_button("Add Student", type="primary")
                if submit_student:
                    if not n_roll or not n_name:
                        st.error("Roll Number and Name are required.")
                    else:
                        with st.spinner("Adding student..."):
                            photo_b64 = base64.b64encode(n_photo.getvalue()).decode() if n_photo else ""
                            s_success, s_result = add_student(
                                class_id=n_class_id, roll_number=n_roll, name=n_name, 
                                apaar_id=n_apaar, reg_number=n_reg, dob=str(n_dob) if n_dob else "", 
                                profile_photo=photo_b64, email=n_email
                            )
                        if s_success:
                            st.success("Successfully added student.")
                            st.rerun()
                        else:
                            st.error(f"Failed to add student: {s_result}")
                            
        with st_tab3:
            st.info("The Excel file must contain these exact column headers: `Roll Number` and `Name of the Learner`")
            st.write("Optional columns: `APAAR ID/PEN`, `Registration/Admission Number`, `Date of Birth` (YYYY-MM-DD), `Email`")
            uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["xlsx", "xls", "csv"])
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                        
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("Confirm Import", type="primary"):
                        with st.spinner("Importing students..."):
                            imp_success, imp_result = bulk_import_students(selected_class_id, df)
                        if imp_success:
                            st.success(imp_result)
                        else:
                            st.error(imp_result)
                except Exception as e:
                    st.error(f"Error reading file: {e}")
