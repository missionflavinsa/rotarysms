import streamlit as st
from src.views.admin_dashboard import render_dashboard
from src.views.admin_teachers import render_teachers
from src.views.admin_classes import render_classes
from src.views.admin_students import render_students
from src.views.admin_results import render_admin_results
from src.views.admin_settings import render_settings

def admin_page():
    # Sidebar navigation for Admin
    page = st.sidebar.radio("Navigation", [
        "📊 Dashboard", 
        "👥 Teachers", 
        "🏫 Classes", 
        "👨‍🎓 Students", 
        "📄 Result Generation",
        "⚙️ Settings"
    ])
    
    st.sidebar.markdown("---")
    
    if page == "📊 Dashboard":
        render_dashboard()
        
    elif page == "👥 Teachers":
        render_teachers()
        
    elif page == "🏫 Classes":
        render_classes()
        
    elif page == "👨‍🎓 Students":
        render_students()
        
    elif page == "📄 Result Generation":
        render_admin_results()
        
    elif page == "⚙️ Settings":
        render_settings()
