import streamlit as st
import pandas as pd
from src.database.firebase_init import create_class, get_all_classes, update_class, delete_class, get_all_users, add_subject, get_subjects, update_subject, delete_subject, log_activity

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
                
                admin_c_t1, admin_c_t2 = st.tabs(["⚙️ Class Settings", "📚 Subjects & Results"])
                
                with admin_c_t1:
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

                with admin_c_t2:
                    st.subheader("📚 Subject Management & Results")
                    
                    # 1. Subject Creation
                    st.write("**➕ Add New Subject**")
                    with st.container(border=True):
                        with st.form(f"admin_add_sub_form_{selected_class_id}"):
                            new_sub_name = st.text_input("Subject Name", placeholder="e.g. Mathematics, Science")
                            add_sub_btn = st.form_submit_button("Create Subject", type="primary")
                            
                            if add_sub_btn:
                                if not new_sub_name:
                                    st.error("Please enter a subject name.")
                                else:
                                    with st.spinner("Creating subject..."):
                                        add_s_success, add_s_res = add_subject(selected_class_id, new_sub_name)
                                    if add_s_success:
                                        log_activity(st.session_state.get('user_email', 'Admin'), "Created Subject", f"{selected_class_data.get('class_name')}-{selected_class_data.get('section')}", f"Added Subject: {new_sub_name}")
                                        st.success("Subject created!")
                                        st.rerun()
                                    else:
                                        st.error(add_s_res)
                    
                    # 2. List Subjects & Manage Results
                    sub_success, subjects = get_subjects(selected_class_id)
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
                                        if st.button("🗑️ Delete Form", key=f"admin_del_sub_{sub['id']}", type="secondary", help="Delete this subject entirely"):
                                            with st.spinner("Deleting..."):
                                                delete_subject(sub['id'])
                                                log_activity(st.session_state.get('user_email', 'Admin'), "Deleted Subject", f"{selected_class_data.get('class_name')}-{selected_class_data.get('section')}", f"Removed Subject: {sub.get('name')}")
                                            st.rerun()
                                                
                                    # Form to update/save the URL
                                    with st.form(f"admin_upd_url_form_{sub['id']}"):
                                        cur_url = st.text_input("Google Sheet URL", value=sub.get('sheet_url', ''), placeholder="https://docs.google.com/spreadsheets/d/...")
                                        save_url_btn = st.form_submit_button("Save Sheet URL")
                                        if save_url_btn:
                                            with st.spinner("Saving..."):
                                                update_subject(sub['id'], sheet_url=cur_url)
                                                log_activity(st.session_state.get('user_email', 'Admin'), "Saved Sheet URL", f"{selected_class_data.get('class_name')}-{selected_class_data.get('section')}", f"Subject: {sub.get('name')}")
                                            st.success("URL Saved!")
                                            st.rerun()
                                    
                                    # If URL is saved, show the fetching logic
                                    saved_url = sub.get('sheet_url', '')
                                    if saved_url:
                                        try:
                                            if "/d/" in saved_url:
                                                doc_id = saved_url.split("/d/")[1].split("/")[0]
                                                export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                                                
                                                cache_key = f"admin_db_tabs_{sub['id']}_{doc_id}"
                                                if cache_key not in st.session_state:
                                                    st.session_state[cache_key] = None
                                                    
                                                col_fetch, col_clear = st.columns([2, 1])
                                                with col_fetch:
                                                    if st.button("Connect & Fetch Tabs", type="primary", key=f"admin_fetch_tabs_{sub['id']}"):
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
                                                        if st.button("Clear Data", key=f"admin_clear_tabs_{sub['id']}"):
                                                            st.session_state[cache_key] = None
                                                            st.rerun()
                                                            
                                                if st.session_state[cache_key] is not None:
                                                    workbook_dict = st.session_state[cache_key]
                                                    tab_names = list(workbook_dict.keys())
                                                    
                                                    selected_tab = st.selectbox("Select Target Tab to View", options=tab_names, key=f"admin_sel_tab_{sub['id']}")
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
        st.error(f"Failed to load classes: {classes_list}")
