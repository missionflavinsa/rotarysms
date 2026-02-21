import streamlit as st
from src.database.firebase_init import sign_in

def login_page():
    st.title("Rotary RMS - Login")
    st.write("Please log in to your account.")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@rems.in")
        password = st.text_input("Password", type="password", placeholder="Enter Password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if not email or not password:
                st.warning("Please enter both email and password")
                return

            if email == "admin@rems.in" and password == "Rotary@123":
                # Admin login successful
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.user_email = email
                st.success("Admin login successful. Redirecting...")
                st.rerun()

            else:
                # Teacher login attempt
                user = sign_in(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "teacher"
                    st.session_state.user_email = email
                    st.success("Login successful. Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Only admin or registered teachers can log in.")
