import streamlit as st

def teacher_page():
    teacher_email = st.session_state.get('user_email', 'Teacher')
    
    # Sidebar navigation for Teacher
    page = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏫 My Classes", "📄 Result Generation", "⚙️ Settings"])
    
    st.sidebar.markdown("---")
    
    if page == "📊 Dashboard":
        from src.views.teacher_dashboard import render_teacher_dashboard
        render_teacher_dashboard(teacher_email)
        
    elif page == "🏫 My Classes":
        from src.views.teacher_classes import render_teacher_classes
        render_teacher_classes(teacher_email)
        
    elif page == "📄 Result Generation":
        from src.views.teacher_results import render_teacher_results
        render_teacher_results(teacher_email)
        
    elif page == "⚙️ Settings":
        from src.views.teacher_settings import render_teacher_settings
        render_teacher_settings(teacher_email)
