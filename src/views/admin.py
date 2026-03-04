import streamlit as st

def admin_page():
    # Sidebar navigation for Admin
    page = st.sidebar.radio("Navigation", [
        "📊 Dashboard", 
        "👥 Teachers", 
        "🏫 Classes", 
        "👨‍🎓 Students", 
        "📄 Result Generation",
        "⚙️ Settings"
    ], key="admin_nav")
    
    st.sidebar.markdown("---")
    
    if page == "📊 Dashboard":
        from src.views.admin_dashboard import render_dashboard
        render_dashboard()
        
    elif page == "👥 Teachers":
        from src.views.admin_teachers import render_teachers
        render_teachers()
        
    elif page == "🏫 Classes":
        from src.views.admin_classes import render_classes
        render_classes()
        
    elif page == "👨‍🎓 Students":
        from src.views.admin_students import render_students
        render_students()
        
    elif page == "📄 Result Generation":
        from src.views.admin_results import render_admin_results
        render_admin_results()
        
    elif page == "⚙️ Settings":
        from src.views.admin_settings import render_settings
        render_settings()
