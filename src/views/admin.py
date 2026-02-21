import streamlit as st
import pandas as pd
from datetime import datetime
from src.database.firebase_init import (create_user, get_all_users, update_user, delete_user, 
                                        create_class, get_all_classes, update_class, delete_class,
                                        add_student, bulk_import_students, get_students_by_class,
                                        update_student, delete_student)

def admin_page():
    st.title("Admin Dashboard")
    st.write("Welcome, Admin. Here you can manage the application.")

    tab1, tab2, tab3, tab4 = st.tabs(["Create Teacher", "Manage Teachers", "Manage Classes", "Manage Students"])
    
    with tab1:
        st.header("Create New Teacher")
        with st.form("create_teacher_form"):
            new_email = st.text_input("Teacher Email")
            new_password = st.text_input("Teacher Password", type="password")
            
            submit_button = st.form_submit_button("Create Teacher Account")
            
            if submit_button:
                if not new_email or not new_password:
                    st.warning("Please provide both email and password.")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating user..."):
                        success, result = create_user(new_email, new_password)
                        
                    if success:
                        st.success(f"Successfully created account for {new_email}")
                    else:
                        st.error(f"Failed to create user: {result}")

    with tab2:
        st.header("Manage Teachers")
        
        success, users_or_error = get_all_users()
        if success:
            if not users_or_error:
                st.info("No teachers found.")
            else:
                # Format data for display
                df = pd.DataFrame(users_or_error)
                # Convert timestamp from milliseconds to readable date
                df['created_at'] = pd.to_datetime(df['created_at'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(df[['email', 'created_at', 'uid']], hide_index=True, use_container_width=True)
                
                # Update / Delete section
                st.subheader("Update or Delete Teacher")
                
                user_options = {u['email']: u['uid'] for u in users_or_error}
                selected_email = st.selectbox("Select Teacher", options=list(user_options.keys()))
                selected_uid = user_options[selected_email]
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.form("update_teacher_form"):
                        st.write("Update Teacher")
                        update_email = st.text_input("New Email", value=selected_email)
                        update_password = st.text_input("New Password", type="password", help="Leave blank to keep current password")
                        update_btn = st.form_submit_button("Update")
                        
                        if update_btn:
                            if not update_email:
                                st.warning("Email cannot be empty.")
                            else:
                                with st.spinner("Updating user..."):
                                    up_success, up_result = update_user(selected_uid, new_email=update_email, new_password=update_password if update_password else None)
                                if up_success:
                                    st.success(f"Successfully updated user {update_email}.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {up_result}")
                
                with col2:
                    with st.form("delete_teacher_form"):
                        st.write("Delete Teacher")
                        st.warning("This action cannot be undone.")
                        delete_btn = st.form_submit_button("Delete Account")
                        
                        if delete_btn:
                            with st.spinner("Deleting user..."):
                                del_success, del_result = delete_user(selected_uid)
                            if del_success:
                                st.success(f"Successfully deleted {selected_email}.")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {del_result}")
        else:
            st.error(f"Failed to load users: {users_or_error}")

    with tab3:
        st.header("Manage Classes")
        
        # We need the list of teachers to assign a class teacher
        t_success, users = get_all_users()
        teacher_emails = [u['email'] for u in users] if t_success and isinstance(users, list) else []
        
        with st.expander("Create New Class", expanded=True):
            with st.form("create_class_form"):
                class_name = st.text_input("Class Name (e.g., 10, 11, 12)")
                section = st.text_input("Section (e.g., A, B, C)")
                
                if not teacher_emails:
                    st.warning("No teachers available. Please create a teacher first in the Create Teacher tab.")
                    selected_teacher = None
                else:
                    selected_teacher = st.selectbox("Assign Class Teacher", options=teacher_emails)
                    
                submit_class = st.form_submit_button("Create Class")
                
                if submit_class:
                    if not class_name or not section:
                        st.warning("Please provide both Class Name and Section.")
                    elif not selected_teacher:
                        st.warning("Please assign a Class Teacher.")
                    else:
                        with st.spinner("Creating class..."):
                            c_success, c_result = create_class(class_name, section, selected_teacher)
                        if c_success:
                            st.success(f"Successfully created Class {class_name}-{section} assigned to {selected_teacher}")
                            st.rerun()
                        else:
                            st.error(f"Failed to create class: {c_result}")
                            
        st.subheader("Existing Classes")
        c_success, classes_list = get_all_classes()
        if c_success:
            if not classes_list:
                st.info("No classes found.")
            else:
                df_classes = pd.DataFrame(classes_list)
                st.dataframe(df_classes[['class_name', 'section', 'teacher_email']], hide_index=True, use_container_width=True)
                
                st.subheader("Update or Delete Class")
                
                # Format options for the selectbox
                class_options = {f"Class {c['class_name']} - Section {c['section']} ({c['teacher_email']})": c['id'] for c in classes_list}
                class_map = {c['id']: c for c in classes_list}
                
                selected_class_label = st.selectbox("Select Class", options=list(class_options.keys()))
                selected_class_id = class_options[selected_class_label]
                selected_class_data = class_map[selected_class_id]
                
                col3, col4 = st.columns(2)
                with col3:
                    with st.form("update_class_form"):
                        st.write("Update Class")
                        u_class_name = st.text_input("Class Name", value=selected_class_data['class_name'])
                        u_section = st.text_input("Section", value=selected_class_data['section'])
                        u_teacher = st.selectbox("Assign Class Teacher", options=teacher_emails, index=teacher_emails.index(selected_class_data['teacher_email']) if selected_class_data['teacher_email'] in teacher_emails else 0)
                        
                        update_c_btn = st.form_submit_button("Update Class")
                        
                        if update_c_btn:
                            if not u_class_name or not u_section or not u_teacher:
                                st.warning("All fields are required.")
                            else:
                                with st.spinner("Updating class..."):
                                    up_c_success, up_c_result = update_class(selected_class_id, class_name=u_class_name, section=u_section, teacher_email=u_teacher)
                                if up_c_success:
                                    st.success("Successfully updated class.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {up_c_result}")
                
                with col4:
                    with st.form("delete_class_form"):
                        st.write("Delete Class")
                        st.warning("This action cannot be undone.")
                        delete_c_btn = st.form_submit_button("Delete Class")
                        
                        if delete_c_btn:
                            with st.spinner("Deleting class..."):
                                del_c_success, del_c_result = delete_class(selected_class_id)
                            if del_c_success:
                                st.success("Successfully deleted class.")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {del_c_result}")
        else:
            st.error(f"Failed to load classes: {classes_list}")

    with tab4:
        st.header("Student Management")
        
        c_success, classes_list = get_all_classes()
        if not c_success or not classes_list:
            st.warning("You must create at least one class before adding students.")
        else:
            class_options = {f"Class {c['class_name']} - Section {c['section']}": c['id'] for c in classes_list}
            selected_class_label = st.selectbox("Select target class:", options=list(class_options.keys()))
            selected_class_id = class_options[selected_class_label]
            
            st.markdown("---")
            st_tab1, st_tab2, st_tab3 = st.tabs(["📋 View & Edit Students", "➕ Add Individual Student", "📁 Bulk Import from Excel"])
            
            with st_tab1:
                st.subheader(f"Students in {selected_class_label}")
                s_success, students = get_students_by_class(selected_class_id)
                
                if s_success:
                    if not students:
                        st.info("No students enrolled in this class.")
                    else:
                        df_students = pd.DataFrame(students)
                        st.dataframe(df_students[['roll_number', 'name', 'email']], hide_index=True, use_container_width=True)
                        
                        st.markdown("---")
                        st.write("**Manage Student Data**")
                        
                        student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
                        student_map = {s['id']: s for s in students}
                        
                        selected_student_label = st.selectbox(f"Select Student", options=list(student_options.keys()), key=f"admin_sel_stu_{selected_class_id}")
                        selected_student_id = student_options[selected_student_label]
                        selected_student_data = student_map[selected_student_id]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.form(f"admin_update_stu_form"):
                                st.write("Update Student")
                                u_roll = st.text_input("Roll Number", value=selected_student_data['roll_number'])
                                u_name = st.text_input("Full Name", value=selected_student_data['name'])
                                u_email = st.text_input("Email", value=selected_student_data.get('email', ''))
                                
                                upd_btn = st.form_submit_button("Update Student", type="primary")
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
                                st.write("Delete Student")
                                st.warning("This action cannot be undone.")
                                del_btn = st.form_submit_button("Delete Student")
                                
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
                st.subheader("Add Individual Student")
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
                st.subheader("Bulk Import via Excel/CSV")
                st.info("Your file must contain a 'Roll Number' column and a 'Name' column. An 'Email' column is optional but supported.")
                uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["xlsx", "xls", "csv"])
                
                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                            
                        st.write("Preview of imported data:")
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
