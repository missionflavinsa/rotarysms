import streamlit as st

def render_teacher_settings(teacher_email):
    st.header("⚙️ Teacher Settings")
    st.write("Manage your personal profile.")
    
    with st.container(border=True):
        st.info("Additional profile settings will be available in a future update.", icon="ℹ️")
        st.text_input("Your Email address", value=teacher_email, disabled=True)
        st.button("Update Profile", disabled=True)
