import streamlit as st
import pandas as pd
from src.database.firebase_init import (get_all_classes, add_student, bulk_import_students, 
                                        get_students_by_class, update_student, delete_student)

def render_students():
    st.header("👨‍🎓 Student Management")
    st.write("Manage student records and class assignments.")
    
    c_success, classes_list = get_all_classes()
    
    if not c_success or not classes_list:
        st.warning("You must create at least one class before adding students.")
    else:
        class_options = {f"Class {c['class_name']} - Section {c['section']}": c['id'] for c in classes_list}
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
                    st.dataframe(df_students[['roll_number', 'name', 'email']], hide_index=True, use_container_width=True)
                    
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
                                u_roll = st.text_input("Roll Number", value=selected_student_data['roll_number'])
                                u_name = st.text_input("Full Name", value=selected_student_data['name'])
                                u_email = st.text_input("Email", value=selected_student_data.get('email', ''))
                                
                                upd_btn = st.form_submit_button("Update Student")
                                if upd_btn:
                                    if not u_roll or not u_name:
                                        st.error("Roll Number and Name are required.")
                                    else:
                                        with st.spinner("Updating student..."):
                                            up_success, up_res = update_student(selected_student_id, roll_number=u_roll, name=u_name, email=u_email)
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
                roll_no = st.text_input("Roll Number")
                name = st.text_input("Full Name")
                email = st.text_input("Email (Optional)")
                
                submit_student = st.form_submit_button("Add Student", type="primary")
                if submit_student:
                    if not roll_no or not name:
                        st.error("Roll Number and Name are required.")
                    else:
                        with st.spinner("Adding student..."):
                            s_success, s_result = add_student(selected_class_id, roll_no, name, email)
                        if s_success:
                            st.success("Successfully added student.")
                            st.rerun()
                        else:
                            st.error(f"Failed to add student: {s_result}")
                            
        with st_tab3:
            st.info("Your file must contain a 'Roll Number' column and a 'Name' column. An 'Email' column is optional.")
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
