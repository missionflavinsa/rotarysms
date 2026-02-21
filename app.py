import streamlit as st

# Set Streamlit Page Config MUST BE FIRST
st.set_page_config(page_title="Rotary RMS", page_icon="🎓", layout="wide")

from src.views.login import login_page
from src.views.admin import admin_page
from src.views.teacher import teacher_page
from src.database.firebase_init import init_firebase

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None # 'admin' or 'teacher'
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def main():
    # Ensure Firebase is initialized
    init_firebase()
    
    # Hide default Streamlit menu and footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    st.sidebar.title("Rotary RMS")
    
    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as: {st.session_state.user_email}")
        if st.sidebar.button("Logout"):
            # Clear session
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_email = None
            st.rerun()
            
        # Routing based on role
        if st.session_state.user_role == 'admin':
            admin_page()
        elif st.session_state.user_role == 'teacher':
            teacher_page()
            
    else:
        login_page()

if __name__ == "__main__":
    main()
