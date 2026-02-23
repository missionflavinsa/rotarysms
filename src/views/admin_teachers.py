import streamlit as st
import pandas as pd
import base64
from src.database.firebase_init import create_user, get_all_users, update_user, delete_user

def render_teachers():
    st.header("👥 Teacher Management")
    st.write("Manage teacher accounts and access.")
    
    with st.expander("➕ Create New Teacher", expanded=False):
        with st.form("create_teacher_form"):
            new_photo = st.file_uploader("Profile Photo", type=["png", "jpg", "jpeg"])
            new_name = st.text_input("Teacher Full Name")
            new_email = st.text_input("Teacher Email")
            new_password = st.text_input("Teacher Password", type="password")
            submit_button = st.form_submit_button("Create Teacher Account", type="primary")
            
            if submit_button:
                if not new_email or not new_password or not new_name:
                    st.warning("Please provide name, email, and password.")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating user..."):
                        photo_b64 = base64.b64encode(new_photo.getvalue()).decode() if new_photo else ""
                        success, result = create_user(new_email, new_password, name=new_name, profile_photo=photo_b64)
                    if success:
                        st.success(f"Successfully created account for {new_name} ({new_email})")
                        st.rerun()
                    else:
                        st.error(f"Failed to create user: {result}")
                        
    st.write("**Existing Teachers**")
    success, users_or_error = get_all_users()
    if success:
        if not users_or_error:
            st.info("No teachers found.")
        else:
            df = pd.DataFrame(users_or_error)
            df['created_at'] = pd.to_datetime(df['created_at'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
            
            display_cols = ['name', 'email', 'created_at'] if 'name' in df.columns else ['email', 'created_at']
            st.dataframe(df[display_cols], hide_index=True, use_container_width=True)
            
            st.write("**Update or Delete Teacher**")
            # Map by Name + Email if name exists, else just Email
            user_options = {f"{u.get('name', 'No Name')} ({u['email']})": u['uid'] for u in users_or_error}
            user_map = {u['uid']: u for u in users_or_error}
            
            with st.container(border=True):
                selected_label = st.selectbox("Select Teacher to modify", options=list(user_options.keys()))
                selected_uid = user_options[selected_label]
                selected_user = user_map[selected_uid]
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.form("update_teacher_form"):
                        st.write("Update Credentials & Profile")
                        up_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"])
                        update_name = st.text_input("Full Name", value=selected_user.get('name', ''))
                        update_email = st.text_input("New Email", value=selected_user['email'])
                        update_password = st.text_input("New Password", type="password", help="Leave blank to keep current")
                        update_btn = st.form_submit_button("Update Teacher")
                        
                        if update_btn:
                            if not update_email or not update_name:
                                st.warning("Name and Email cannot be empty.")
                            else:
                                with st.spinner("Updating user..."):
                                    photo_b64 = selected_user.get('profile_photo', '')
                                    if up_photo:
                                        photo_b64 = base64.b64encode(up_photo.getvalue()).decode()
                                        
                                    up_success, up_result = update_user(
                                        selected_uid, 
                                        new_email=update_email, 
                                        new_password=update_password if update_password else None,
                                        name=update_name,
                                        profile_photo=photo_b64
                                    )
                                if up_success:
                                    st.success(f"Successfully updated user.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {up_result}")
                with col2:
                    with st.form("delete_teacher_form"):
                        st.write("Delete Account")
                        st.warning("This action cannot be undone.")
                        delete_btn = st.form_submit_button("Delete Teacher", type="primary")
                        
                        if delete_btn:
                            with st.spinner("Deleting user..."):
                                del_success, del_result = delete_user(selected_uid)
                            if del_success:
                                st.success(f"Successfully deleted {selected_email}.")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {del_result}")
    else:
        st.error(f"Failed to load users: {users_or_error}")
