import streamlit as st
import pandas as pd
from src.database.firebase_init import create_class, get_all_classes, update_class, delete_class, get_all_users

def render_classes():
    st.header("🏫 Class Management")
    st.write("Create and assign classes to teachers.")
    
    t_success, users = get_all_users()
    teacher_emails = [u['email'] for u in users] if t_success and isinstance(users, list) else []
    
    with st.expander("➕ Create New Class", expanded=False):
        with st.form("create_class_form"):
            class_name = st.text_input("Class Name (e.g., 10, 11, 12)")
            section = st.text_input("Section (e.g., A, B, C)")
            selected_teacher = st.selectbox("Assign Class Teacher", options=teacher_emails) if teacher_emails else None
            if not teacher_emails:
                st.warning("No teachers available. Please create a teacher first.")
                
            submit_class = st.form_submit_button("Create Class", type="primary")
            if submit_class:
                if not class_name or not section or not selected_teacher:
                    st.warning("Please provide all fields.")
                else:
                    with st.spinner("Creating class..."):
                        c_success, c_result = create_class(class_name, section, selected_teacher)
                    if c_success:
                        st.success("Successfully created Class!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create class: {c_result}")
                        
    st.write("**Existing Classes**")
    c_success, classes_list = get_all_classes()
    if c_success:
        if not classes_list:
            st.info("No classes found.")
        else:
            df_classes = pd.DataFrame(classes_list)
            st.dataframe(df_classes[['class_name', 'section', 'teacher_email']], hide_index=True, use_container_width=True)
            
            st.write("**Update or Delete Class**")
            class_options = {f"Class {c['class_name']} - Section {c['section']} ({c['teacher_email']})": c['id'] for c in classes_list}
            class_map = {c['id']: c for c in classes_list}
            
            with st.container(border=True):
                selected_class_label = st.selectbox("Select Class to modify", options=list(class_options.keys()))
                selected_class_id = class_options[selected_class_label]
                selected_class_data = class_map[selected_class_id]
                
                col3, col4 = st.columns(2)
                with col3:
                    with st.form("update_class_form"):
                        u_class_name = st.text_input("Class Name", value=selected_class_data['class_name'])
                        u_section = st.text_input("Section", value=selected_class_data['section'])
                        u_teacher = st.selectbox("Assign Teacher", options=teacher_emails, index=teacher_emails.index(selected_class_data['teacher_email']) if selected_class_data['teacher_email'] in teacher_emails else 0)
                        
                        update_c_btn = st.form_submit_button("Update Class")
                        if update_c_btn:
                            if not u_class_name or not u_section or not u_teacher:
                                st.warning("All fields are required.")
                            else:
                                with st.spinner("Updating class..."):
                                    up_c_success, up_c_res = update_class(selected_class_id, class_name=u_class_name, section=u_section, teacher_email=u_teacher)
                                if up_c_success:
                                    st.success("Class updated.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {up_c_res}")
                with col4:
                    with st.form("delete_class_form"):
                        st.write('<div style="height: 38px;"></div>', unsafe_allow_html=True) # Formatting spacer
                        st.warning("This action cannot be undone.")
                        delete_c_btn = st.form_submit_button("Delete Class", type="primary")
                        if delete_c_btn:
                            with st.spinner("Deleting class..."):
                                    del_c_success, del_c_res = delete_class(selected_class_id)
                            if del_c_success:
                                st.success("Class deleted.")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {del_c_res}")
    else:
        st.error(f"Failed to load classes: {classes_list}")
