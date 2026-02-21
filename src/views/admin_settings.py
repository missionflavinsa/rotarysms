import streamlit as st
import base64
from src.database.firebase_init import (get_org_logo, update_org_logo, get_org_name, 
                                        update_org_name, get_admin_credentials, update_admin_credentials)

def render_settings():
    st.header("⚙️ Organization Settings")
    st.write("Manage your school's structural settings and preferences.")
    
    st.subheader("Administrator Settings")
    
    # Fetch current config
    current_org_name = get_org_name()
    admin_success, admin_email, admin_password = get_admin_credentials()
    
    with st.container(border=True):
        st.write("**System Profile**")
        with st.form("admin_profile_form"):
            new_org_name = st.text_input("Organization Name", value=current_org_name)
            new_admin_email = st.text_input("Admin Email", value=admin_email if admin_success else "")
            new_admin_password = st.text_input("Admin Password", value=admin_password if admin_success else "", type="password")
            
            update_sys_btn = st.form_submit_button("Update Profile", type="primary")
            if update_sys_btn:
                if not new_admin_email or not new_admin_password or not new_org_name:
                    st.error("All fields are required.")
                else:
                    with st.spinner("Updating profile..."):
                        up_org_success, up_org_res = update_org_name(new_org_name)
                        up_adm_success, up_adm_res = update_admin_credentials(new_admin_email, new_admin_password)
                        
                    if up_org_success and up_adm_success:
                        st.session_state.org_name = new_org_name
                        st.session_state.user_email = new_admin_email
                        st.success("System Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update profile: {up_org_res} / {up_adm_res}")
        
        st.markdown("---")
        st.write("**Organization Logo**")
        
        # Fetch current logo to preview
        l_success, current_logo = get_org_logo()
        if l_success and current_logo:
            st.image(f"data:image/png;base64,{current_logo}", width=150)
        
        uploaded_logo = st.file_uploader("Upload New Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo is not None:
            st.image(uploaded_logo, caption="Preview of New Logo", width=150)
            if st.button("Save New Logo", type="primary"):
                with st.spinner("Saving logo..."):
                    # Convert to base64
                    bytes_data = uploaded_logo.getvalue()
                    base64_str = base64.b64encode(bytes_data).decode()
                    up_success, up_res = update_org_logo(base64_str)
                    if up_success:
                        st.session_state.org_logo = base64_str
                        st.success("Logo updated successfully! (It is now visible in the sidebar)")
                        st.rerun()
                    else:
                        st.error(f"Failed to save logo: {up_res}")
