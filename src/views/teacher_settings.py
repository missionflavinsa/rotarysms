import streamlit as st
import base64
from src.database.firebase_init import get_all_users, update_user

def render_teacher_settings(teacher_email):
    st.header("⚙️ Teacher Settings")
    st.write("Manage your personal profile and credentials.")
    
    # Needs to find the teacher's UID and data
    success, users = get_all_users()
    if not success or not users:
        st.error("Failed to load user profile data.")
        return
        
    current_user = next((u for u in users if u['email'] == teacher_email), None)
    if not current_user:
        st.error("Current user not found in database.")
        st.stop()
        
    with st.container(border=True):
        with st.form("teacher_self_update_form"):
            st.subheader("Profile Information")
            up_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"])
            
            update_name = st.text_input("Full Name", value=current_user.get('name', ''))
            update_email = st.text_input("Email Address", value=current_user['email'])
            
            st.write("---")
            st.subheader("Security")
            update_password = st.text_input("New Password", type="password", help="Leave blank to keep your current password")
            
            submit_btn = st.form_submit_button("Save Changes", type="primary")
            if submit_btn:
                if not update_email or not update_name:
                    st.warning("Name and Email cannot be empty.")
                else:
                    with st.spinner("Updating profile..."):
                        photo_b64 = current_user.get('profile_photo', '')
                        if up_photo:
                            photo_b64 = base64.b64encode(up_photo.getvalue()).decode()
                            
                        up_success, up_result = update_user(
                            current_user['uid'], 
                            new_email=update_email, 
                            new_password=update_password if update_password else None,
                            name=update_name,
                            profile_photo=photo_b64
                        )
                    if up_success:
                        st.session_state['user_email'] = update_email
                        st.success("Successfully updated profile details.")
                        st.rerun()
                    else:
                        st.error(f"Update failed: {up_result}")
