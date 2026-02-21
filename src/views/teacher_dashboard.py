import streamlit as st
import pandas as pd
from src.database.firebase_init import get_classes_for_teacher, get_students_by_class, get_subjects

def render_teacher_dashboard(teacher_email):
    st.header("📊 Teacher Overview")
    st.write("Welcome to your interactive Rotary RMS dashboard.")
    
    success, classes = get_classes_for_teacher(teacher_email)
    
    # Calculate Metrics
    total_classes = 0
    total_students = 0
    total_subjects = 0
    active_sheets = 0
    
    if success and classes:
        total_classes = len(classes)
        for c in classes:
            s_success, students = get_students_by_class(c['id'])
            if s_success:
                total_students += len(students)
                
            sub_success, subjects = get_subjects(c['id'])
            if sub_success:
                total_subjects += len(subjects)
                active_sheets += sum(1 for sub in subjects if sub.get('sheet_url', '').strip() != "")
                
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with st.container(border=True):
        m_col1.metric("Assigned Classes", total_classes)
    with st.container(border=True):
        m_col2.metric("Total Students Enrolled", total_students)
    with st.container(border=True):
        m_col3.metric("Subjects Managed", total_subjects)
    with st.container(border=True):
        m_col4.metric("Active Result Sheets", active_sheets)
        
    st.markdown("---")
    st.subheader("Recent Activity")
    st.info("Your recent class management activities will appear here in a future update.")
