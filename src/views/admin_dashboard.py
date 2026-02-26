import streamlit as st
import pandas as pd
from datetime import datetime
from src.database.firebase_init import (get_all_users, get_all_classes, 
                                        get_students_by_class, get_subjects, get_recent_logs)

def render_dashboard():
    st.header("📈 Teacher Activity Dashboard")
    st.write("Monitor teacher metrics and view an audit log of recent actions.")
    
    t_success, users = get_all_users()
    teacher_emails = ["All Teachers"] + [u['email'] for u in users] if t_success and isinstance(users, list) else ["All Teachers"]
    
    selected_target = st.selectbox("Select Teacher to View", options=teacher_emails)
    
    st.markdown("---")
    st.subheader(f"Activity Metrics for {selected_target}")
    
    c_success, classes_list = get_all_classes()
    
    # Accumulate Detailed Data
    active_classes_data = []
    active_students_data = []
    active_subjects_data = []
    
    if c_success and classes_list:
        for c in classes_list:
            if selected_target == "All Teachers" or c.get('teacher_email') == selected_target:
                c_label = f"{c.get('class_name')}-{c.get('section')}"
                t_email = c.get('teacher_email')
                
                active_classes_data.append({
                    "Class": c_label,
                    "Teacher": t_email
                })
                
                s_success, students = get_students_by_class(c['id'])
                if s_success:
                    for st_rec in students:
                        active_students_data.append({
                            "Roll No": st_rec.get('roll_number'),
                            "Name": st_rec.get('name'),
                            "Class": c_label,
                            "Teacher": t_email
                        })
                        
                sub_success, subjects = get_subjects(c['id'])
                if sub_success:
                    for sub in subjects:
                        active_subjects_data.append({
                            "Subject Name": sub.get('name'),
                            "Term 1 URL": sub.get('sheet_url_t1', ''),
                            "Term 2 URL": sub.get('sheet_url_t2', ''),
                            "Class": c_label,
                            "Teacher": t_email
                        })
                        
    # Calculate Metrics from detailed lists
    total_classes = len(active_classes_data)
    total_students = len(active_students_data)
    total_subjects = len(active_subjects_data)
    active_sheet_links = sum(1 for sub in active_subjects_data if str(sub.get('Term 1 URL', '')).strip() != "" or str(sub.get('Term 2 URL', '')).strip() != "")
                    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Assigned Classes", total_classes)
    m_col2.metric("Total Students Enrolled", total_students)
    m_col3.metric("Subjects Created", total_subjects)
    m_col4.metric("Active Results Sheets", active_sheet_links)
    
    st.markdown("---")
    st.subheader(f"Detailed Data Directory for {selected_target}")
    
    data_tab1, data_tab2, data_tab3 = st.tabs(["📚 Assigned Classes", "👥 Enrolled Students", "🔗 Subjects & Sheets Links"])
    
    with data_tab1:
        if active_classes_data:
            st.dataframe(pd.DataFrame(active_classes_data), hide_index=True, use_container_width=True)
        else:
            st.info("No classes assigned.")
            
    with data_tab2:
        if active_students_data:
            st.dataframe(pd.DataFrame(active_students_data), hide_index=True, use_container_width=True)
        else:
            st.info("No students enrolled.")
            
    with data_tab3:
        if active_subjects_data:
            st.dataframe(pd.DataFrame(active_subjects_data), hide_index=True, use_container_width=True)
        else:
            st.info("No subjects or links created.")
    
    st.markdown("---")
    st.subheader("Recent Actions (Past 24 Hours)")
    
    query_email = None if selected_target == "All Teachers" else selected_target
    log_success, logs = get_recent_logs(query_email, hours=24)
    
    if log_success:
        if not logs:
            st.info("No activity logged in the past 24 hours.")
        else:
            df_logs = pd.DataFrame(logs)
            # Reorder columns for better presentation
            if 'teacher_email' in df_logs.columns and 'timestamp_str' in df_logs.columns:
                df_logs = df_logs[['timestamp_str', 'teacher_email', 'action', 'class_name', 'details']]
                df_logs = df_logs.rename(columns={
                    'timestamp_str': 'Date/Time',
                    'teacher_email': 'Teacher Email',
                    'action': 'Action Performed',
                    'class_name': 'Target Class',
                    'details': 'Details'
                })
            st.dataframe(df_logs, hide_index=True, use_container_width=True)
            
            csv = df_logs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Activity Logs CSV",
                data=csv,
                file_name=f"teacher_activity_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.error(f"Failed to fetch activity logs: {logs}")
