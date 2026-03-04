import streamlit as st
import time

def trace(msg):
    with open("trace_perf.txt", "a") as f:
        f.write(f"{time.time()}: {msg}\n")

trace("--- APP START ---")
# Set Streamlit Page Config MUST BE FIRST
st.set_page_config(page_title="Rotary RMS", page_icon="🎓", layout="wide")

trace("Importing login")
from src.views.login import login_page
trace("Importing admin")
from src.views.admin import admin_page
trace("Importing teacher")
from src.views.teacher import teacher_page
trace("Importing search")
from src.views.universal_search import render_universal_search
trace("Importing db")
from src.database.firebase_init import init_firebase, get_org_logo, get_org_name
trace("Importing utils")
from src.views.ui_utils import inject_custom_css, inject_theme_toggle

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None # 'admin' or 'teacher'
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

from src.views.ui_utils import inject_custom_css, inject_theme_toggle

def main():
    trace("> init_firebase")
    # Ensure Firebase is initialized
    init_firebase()
    
    trace("> inject_custom_css")
    # Inject Global SaaS CSS
    inject_custom_css()
    trace("> hidden styles")
    # Hide default Streamlit menu and footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Dynamically inject organization logo and name
    if 'org_logo' not in st.session_state:
        l_success, logo_b64 = get_org_logo()
        st.session_state.org_logo = logo_b64 if l_success and logo_b64 else None
        
    if 'org_name' not in st.session_state:
        st.session_state.org_name = get_org_name()
        
    if st.session_state.org_logo:
        st.sidebar.markdown(f'<div style="text-align: center; margin-bottom: -20px;"><img src="data:image/png;base64,{st.session_state.org_logo}" style="max-width: 100%; max-height: 120px; border-radius: 8px;"></div>', unsafe_allow_html=True)
    else:
        st.sidebar.title(f"🏢 {st.session_state.org_name}")
        
    if st.session_state.logged_in:
        trace("> render_universal_search")
        st.sidebar.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        render_universal_search()
        
        trace("> user routing")
        st.sidebar.markdown(f'<div style="margin-top: -15px; margin-bottom: -15px;"><small>Logged in as: <b>{st.session_state.user_email}</b></small></div>', unsafe_allow_html=True)
            
        # Routing based on role (renders their specific sidebar nav first)
        if st.session_state.user_role == 'admin':
            trace("> admin_page start")
            admin_page()
            trace("> admin_page end")
        elif st.session_state.user_role == 'teacher':
            trace("> teacher_page start")
            teacher_page()
            trace("> teacher_page end")
            
        st.sidebar.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
        
        # Inject custom CSS specifically to right-align the toggle
        st.sidebar.markdown("""
            <style>
            [data-testid="stSidebar"] [data-testid="stToggle"] {
                display: flex;
                justify-content: flex-end;
                padding-right: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        inject_theme_toggle()
            
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Clear session
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_email = None
            st.rerun()
            
    else:
        login_page()

if __name__ == "__main__":
    trace("--- main() start ---")
    main()
    trace("--- main() end ---")
