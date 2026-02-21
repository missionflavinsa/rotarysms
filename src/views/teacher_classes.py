import streamlit as st
import pandas as pd
from src.database.firebase_init import get_classes_for_teacher, get_students_by_class, update_student, delete_student, add_subject, get_subjects, update_subject, delete_subject, log_activity

def render_teacher_classes(teacher_email):
    st.header("🏫 My Assigned Classes")
    st.write("Manage students and academic subjects.")
    
    success, classes = get_classes_for_teacher(teacher_email)
    
    if success:
        if not classes:
            st.info("You are not assigned as a Class Teacher to any class yet.")
        else:
            # Display classes as horizontal tabs
            class_tabs = st.tabs([f"Class {c.get('class_name')} - {c.get('section')}" for c in classes])
            
            for idx, cls in enumerate(classes):
                with class_tabs[idx]:
                    st.write(f"Management Panel for **Class {cls.get('class_name')}-{cls.get('section')}**")
                    
                    inner_tab1, inner_tab2 = st.tabs(["👥 Student Roster", "📚 Subjects & Results"])
                    
                    with inner_tab1:
                        st.subheader("Students List")
                        s_success, students = get_students_by_class(cls['id'])
                        
                        if s_success:
                            if not students:
                                st.info("No students enrolled in this class.")
                            else:
                                df_students = pd.DataFrame(students)
                                st.dataframe(df_students[['roll_number', 'name', 'email']], hide_index=True, use_container_width=True)
                                
                                st.write("**Manage Student Data**")
                                with st.container(border=True):
                                    student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
                                    student_map = {s['id']: s for s in students}
                                    
                                    selected_student_label = st.selectbox(f"Select Student from {cls['class_name']}-{cls['section']}", options=list(student_options.keys()), key=f"sel_{cls['id']}")
                                    selected_student_id = student_options[selected_student_label]
                                    selected_student_data = student_map[selected_student_id]
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        with st.form(f"update_student_form_{cls['id']}"):
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
                                                        log_activity(teacher_email, "Updated Student", f"{cls.get('class_name')}-{cls.get('section')}", f"Roll: {u_roll}, Name: {u_name}")
                                                        st.success("Successfully updated student.")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"Failed to update: {up_res}")
                                                        
                                    with col2:
                                        with st.form(f"delete_student_form_{cls['id']}"):
                                            st.write('<div style="height: 38px;"></div>', unsafe_allow_html=True)
                                            st.warning("This action cannot be undone.")
                                            del_btn = st.form_submit_button("Delete Student")
                                            
                                            if del_btn:
                                                with st.spinner("Deleting student..."):
                                                    del_success, del_res = delete_student(selected_student_id)
                                                if del_success:
                                                    log_activity(teacher_email, "Deleted Student", f"{cls.get('class_name')}-{cls.get('section')}", f"Roll: {selected_student_data.get('roll_number')}")
                                                    st.success("Successfully deleted student.")
                                                    st.rerun()
                                                else:
                                                    st.error(f"Failed to delete: {del_res}")
                        else:
                            st.error(f"Failed to load students: {students}")
                            
                    with inner_tab2:
                        st.subheader("📚 Subject Management & Results")
                        
                        # 1. Subject Creation
                        st.write("**➕ Add New Subject**")
                        with st.container(border=True):
                            with st.form(f"add_sub_form_{cls['id']}"):
                                new_sub_name = st.text_input("Subject Name", placeholder="e.g. Mathematics, Science")
                                add_sub_btn = st.form_submit_button("Create Subject", type="primary")
                                
                                if add_sub_btn:
                                    if not new_sub_name:
                                        st.error("Please enter a subject name.")
                                    else:
                                        with st.spinner("Creating subject..."):
                                            add_s_success, add_s_res = add_subject(cls['id'], new_sub_name)
                                        if add_s_success:
                                            log_activity(teacher_email, "Created Subject", f"{cls.get('class_name')}-{cls.get('section')}", f"Added Subject: {new_sub_name}")
                                            st.success("Subject created!")
                                            st.rerun()
                                        else:
                                            st.error(add_s_res)
                        
                        # 2. List Subjects & Manage Results
                        sub_success, subjects = get_subjects(cls['id'])
                        if sub_success:
                            if not subjects:
                                st.info("No subjects created yet for this class.")
                            else:
                                st.write("**Manage Subject Results**")
                                # Create a tab for each subject
                                sub_tabs = st.tabs([sub['name'] for sub in subjects])
                                
                                for s_idx, sub in enumerate(subjects):
                                    with sub_tabs[s_idx]:
                                        c_col1, c_col2 = st.columns([5, 1])
                                        with c_col1:
                                            st.info("Paste the public Google Sheet link uniquely for this subject.")
                                        with c_col2:
                                            if st.button("🗑️ Delete Form", key=f"del_sub_{sub['id']}", type="secondary", help="Delete this subject entirely"):
                                                with st.spinner("Deleting..."):
                                                    delete_subject(sub['id'])
                                                    log_activity(teacher_email, "Deleted Subject", f"{cls.get('class_name')}-{cls.get('section')}", f"Removed Subject: {sub.get('name')}")
                                                st.rerun()
                                                    
                                        # Form to update/save the URL
                                        with st.form(f"upd_url_form_{sub['id']}"):
                                            cur_url = st.text_input("Google Sheet URL", value=sub.get('sheet_url', ''), placeholder="https://docs.google.com/spreadsheets/d/...")
                                            save_url_btn = st.form_submit_button("Save Sheet URL")
                                            if save_url_btn:
                                                with st.spinner("Saving..."):
                                                    update_subject(sub['id'], sheet_url=cur_url)
                                                    log_activity(teacher_email, "Saved Sheet URL", f"{cls.get('class_name')}-{cls.get('section')}", f"Subject: {sub.get('name')}")
                                                st.success("URL Saved!")
                                                st.rerun()
                                        
                                        # If URL is saved, show the fetching logic
                                        saved_url = sub.get('sheet_url', '')
                                        if saved_url:
                                            try:
                                                if "/d/" in saved_url:
                                                    doc_id = saved_url.split("/d/")[1].split("/")[0]
                                                    export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                                                    
                                                    cache_key = f"db_tabs_{sub['id']}_{doc_id}"
                                                    if cache_key not in st.session_state:
                                                        st.session_state[cache_key] = None
                                                        
                                                    col_fetch, col_clear = st.columns([2, 1])
                                                    with col_fetch:
                                                        if st.button("Connect & Fetch Tabs", type="primary", key=f"fetch_tabs_{sub['id']}"):
                                                            with st.spinner(f"Downloading {sub['name']} Sheet..."):
                                                                try:
                                                                    raw_dict = pd.read_excel(export_url, sheet_name=None)
                                                                    clean_dict = {}
                                                                    for t_name, df in raw_dict.items():
                                                                        clean_dict[t_name] = df.fillna("").astype(str)
                                                                    st.session_state[cache_key] = clean_dict
                                                                    st.success("Successfully fetched workbook!")
                                                                    st.rerun()
                                                                except Exception as e:
                                                                    st.error(f"Error accessing sheet data: {e} - Check link permissions.")
                                                    with col_clear:
                                                        if st.session_state[cache_key] is not None:
                                                            if st.button("Clear Data", key=f"clear_tabs_{sub['id']}"):
                                                                st.session_state[cache_key] = None
                                                                st.rerun()
                                                                
                                                    if st.session_state[cache_key] is not None:
                                                        workbook_dict = st.session_state[cache_key]
                                                        tab_names = list(workbook_dict.keys())
                                                        
                                                        selected_tab = st.selectbox("Select Target Tab to View", options=tab_names, key=f"sel_tab_{sub['id']}")
                                                        if selected_tab:
                                                            df_results = workbook_dict[selected_tab]
                                                            if df_results.empty:
                                                                st.warning(f"The tab '{selected_tab}' appears to be empty.")
                                                            else:
                                                                st.dataframe(df_results, hide_index=True, use_container_width=True)
                                                else:
                                                    st.warning("Invalid Google Sheet URL format. Please paste the full URL containing '/d/...'.")
                                            except Exception as main_e:
                                                st.error(f"An unexpected error occurred: {main_e}")
                        else:
                            st.error("Failed to load subjects.")
    else:
        st.error(f"Failed to load your assigned classes: {classes}")
