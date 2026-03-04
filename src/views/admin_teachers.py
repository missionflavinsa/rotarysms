import streamlit as st
import pandas as pd
import io
import requests
import base64
from src.database.firebase_init import create_user, get_all_users, update_user, delete_user

def render_teachers():
    st.header("👥 Teacher Management")
    st.write("Manage teacher accounts and access.")
    
    with st.expander("➕ Create New Teacher", expanded=False):
        with st.form("create_teacher_form"):
            new_photo = st.file_uploader("Profile Photo", type=["png", "jpg", "jpeg"])
            new_signature = st.file_uploader("Upload Teacher Signature", type=["png", "jpg", "jpeg"], key="new_sig")
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
                        from src.utils.image_utils import process_uploaded_image
                        photo_b64 = process_uploaded_image(new_photo) if new_photo else ""
                        sig_b64 = process_uploaded_image(new_signature) if new_signature else ""
                        success, result = create_user(new_email, new_password, name=new_name, profile_photo=photo_b64, signature=sig_b64)
                    if success:
                        st.success(f"Successfully created account for {new_name} ({new_email})")
                        st.rerun()
                    else:
                        st.error(f"Failed to create user: {result}")
                        
    with st.expander("📁 Bulk Excel Upload", expanded=False):
        st.write("Import multiple teachers at once using an Excel file.")
        
        # 1. Download Sample
        st.write("**Step 1: Download Template**")
        sample_df = pd.DataFrame(columns=[
            'Teacher Full Name', 'Teacher Email', 'Teacher Password', 'Profile Photo URL', 'Signature Photo URL'
        ])
        
        sample_buffer = io.BytesIO()
        with pd.ExcelWriter(sample_buffer, engine='openpyxl') as writer:
            sample_df.to_excel(writer, index=False)
        sample_buffer.seek(0)
        
        st.download_button(
            label="⬇️ Download Sample Excel",
            data=sample_buffer,
            file_name="Bulk_Teacher_Import_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 2. Upload and Process
        st.write("---")
        st.write("**Step 2: Upload Completed File**")
        uploaded_excel = st.file_uploader("Upload filled Excel Template", type=["xlsx", "xls"])
        
        if uploaded_excel is not None:
            if st.button("🚀 Import Teachers", type="primary"):
                try:
                    df_import = pd.read_excel(uploaded_excel)
                    total_rows = len(df_import)
                    
                    if total_rows == 0:
                        st.warning("The uploaded Excel file is empty.")
                    else:
                        st.write(f"Found {total_rows} records. Beginning import...")
                        progress_bar = st.progress(0)
                        
                        success_count = 0
                        error_count = 0
                        
                        for index, row in df_import.iterrows():
                            # Extract data cleanly
                            name = str(row.get('Teacher Full Name', '')).strip()
                            email = str(row.get('Teacher Email', '')).strip()
                            password = str(row.get('Teacher Password', '')).strip()
                            photo_url = str(row.get('Profile Photo URL', '')).strip()
                            sig_url = str(row.get('Signature Photo URL', '')).strip()
                            
                            # Clean up NaNs
                            if name.lower() == 'nan': name = ''
                            if email.lower() == 'nan': email = ''
                            if password.lower() == 'nan': password = ''
                            if photo_url.lower() == 'nan': photo_url = ''
                            if sig_url.lower() == 'nan': sig_url = ''
                            
                            if not email or not password or not name:
                                st.error(f"Row {index + 2}: Missing required fields (Name, Email, or Password). Skipping.")
                                error_count += 1
                                continue
                                
                            # Convert Image URLs to base64
                            photo_b64 = ""
                            if photo_url and (photo_url.startswith("http://") or photo_url.startswith("https://")):
                                try:
                                    resp = requests.get(photo_url, timeout=5)
                                    if resp.status_code == 200:
                                        from src.utils.image_utils import process_uploaded_image
                                        import io
                                        photo_b64 = process_uploaded_image(io.BytesIO(resp.content))
                                except Exception as e:
                                    st.warning(f"Row {index + 2}: Failed to fetch Profile Photo: {e}")
                                    
                            sig_b64 = ""
                            if sig_url and (sig_url.startswith("http://") or sig_url.startswith("https://")):
                                try:
                                    resp = requests.get(sig_url, timeout=5)
                                    if resp.status_code == 200:
                                        from src.utils.image_utils import process_uploaded_image
                                        import io
                                        sig_b64 = process_uploaded_image(io.BytesIO(resp.content))
                                except Exception as e:
                                    st.warning(f"Row {index + 2}: Failed to fetch Signature Photo: {e}")
                            
                            # Create Firebase Auth User
                            c_success, c_result = create_user(
                                email=email, 
                                password=password, 
                                name=name, 
                                profile_photo=photo_b64, 
                                signature=sig_b64
                            )
                            
                            if c_success:
                                success_count += 1
                            else:
                                st.error(f"Row {index + 2}: Firebase failed for {email} -> {c_result}")
                                error_count += 1
                                
                            # Update Progress
                            progress_bar.progress((index + 1) / total_rows)
                            
                        if success_count > 0:
                            st.success(f"Successfully imported {success_count} teachers!")
                        if error_count > 0:
                            st.warning(f"Failed to import {error_count} teachers. Check errors above.")
                            
                except Exception as e:
                    st.error(f"Failed to parse Excel file: {e}")
                    
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
                        up_signature = st.file_uploader("Update Teacher Signature", type=["png", "jpg", "jpeg"], key="up_sig")
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
                                    sig_b64 = selected_user.get('signature', '')
                                    if up_photo:
                                        from src.utils.image_utils import process_uploaded_image
                                        photo_b64 = process_uploaded_image(up_photo)
                                    if up_signature:
                                        from src.utils.image_utils import process_uploaded_image
                                        sig_b64 = process_uploaded_image(up_signature)
                                        
                                    up_success, up_result = update_user(
                                        selected_uid, 
                                        new_email=update_email, 
                                        new_password=update_password if update_password else None,
                                        name=update_name,
                                        profile_photo=photo_b64,
                                        signature=sig_b64
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
