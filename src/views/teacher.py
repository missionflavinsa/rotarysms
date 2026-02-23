import streamlit as st
from src.views.teacher_dashboard import render_teacher_dashboard
from src.views.teacher_classes import render_teacher_classes
from src.views.teacher_results import render_teacher_results
from src.views.teacher_settings import render_teacher_settings

def teacher_page():
    teacher_email = st.session_state.get('user_email', 'Teacher')
    
    # Sidebar navigation for Teacher
    page = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏫 My Classes", "📄 Result Generation", "⚙️ Settings"])
    
    st.sidebar.markdown("---")
    
    if page == "📊 Dashboard":
        render_teacher_dashboard(teacher_email)
        
    elif page == "🏫 My Classes":
        render_teacher_classes(teacher_email)
        
    elif page == "📄 Result Generation":
        render_teacher_results(teacher_email)
        
    elif page == "⚙️ Settings":
        render_teacher_settings(teacher_email)
