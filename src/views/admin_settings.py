import streamlit as st
import base64
from src.database.firebase_init import (get_org_logo, update_org_logo, get_org_name, 
                                        update_org_name, get_admin_credentials, update_admin_credentials,
                                        get_org_settings, update_org_settings)
from src.views.admin_results import get_available_fonts

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
                    bytes_data = uploaded_logo.getvalue()
                    base64_str = base64.b64encode(bytes_data).decode()
                    up_success, up_res = update_org_logo(base64_str)
                    if up_success:
                        st.session_state.org_logo = base64_str
                        st.success("Logo updated successfully! (It is now visible in the sidebar)")
                        st.rerun()
                    else:
                        st.error(f"Failed to save logo: {up_res}")

    # Fetch extended Organization Settings
    s_success, org_settings = get_org_settings()
    if not org_settings: org_settings = {}
    
    available_fonts = get_available_fonts()
    font_names = list(available_fonts.keys())
    
    def get_font_index(alias):
        if not alias: return 0
        for i, (k, v) in enumerate(available_fonts.items()):
            if v == alias: return i
        return 0
    
    st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    st.subheader("Academic & Structural Settings")
    
    with st.container(border=True):
        with st.form("org_extended_settings_form"):
            st.write("**Report Card Headings**")
            
            # --- Academic Year Settings ---
            colA1, colA2, colA3 = st.columns(3)
            with colA1:
                ay_val = st.text_input("Academic Year (e.g. 2025-2026)", value=org_settings.get("academic_year", ""))
            with colA2:
                ay_font_size = st.number_input("Font Size", min_value=6, max_value=30, value=org_settings.get("academic_year_size", 12))
            with colA3:
                ay_font_fam = st.selectbox("Font Family", font_names, index=get_font_index(org_settings.get("academic_year_family")))
                
            st.markdown("---")
            
            # --- Session and Timing Settings ---
            st.write("**Session & Timings**")
            colS1, colS2, colS3 = st.columns(3)
            with colS1:
                import datetime
                # Parse existing date or default to today
                default_d = datetime.date.today()
                saved_d = org_settings.get("session_date", "")
                if saved_d:
                    try:
                        default_d = datetime.datetime.strptime(saved_d, "%d/%m/%Y").date()
                    except:
                        pass
                sess_val = st.date_input("New Session Date", value=default_d, format="DD/MM/YYYY")
            with colS2:
                sess_font_size = st.number_input("Session Font Size", min_value=6, max_value=30, value=org_settings.get("session_size", 10), key="s_size")
            with colS3:
                sess_font_fam = st.selectbox("Session Font", font_names, index=get_font_index(org_settings.get("session_family")), key="s_fam")
            
            st.write("Timings")
            colT1, colT2, colT3, colT4 = st.columns(4)
            with colT1:
                time_from = st.text_input("From:", value=org_settings.get("time_from", "08:00 AM"))
            with colT2:
                time_to = st.text_input("To:", value=org_settings.get("time_to", "01:00 PM"))
            with colT3:
                time_font_size = st.number_input("Time Font Size", min_value=6, max_value=30, value=org_settings.get("time_size", 10), key="t_size")
            with colT4:
                time_font_fam = st.selectbox("Time Font", font_names, index=get_font_index(org_settings.get("time_family")), key="t_fam")
                
            st.markdown("---")
            
            # --- Personnel Signatures ---
            st.write("**Personnel & Signatures**")
            st.info("Upload signatures as PNG/JPG with white or transparent backgrounds.")
            
            coord_titles = [
                ("Primary Coordinator", "coord_primary"),
                ("Secondary Coordinator", "coord_secondary"),
                ("Senior Secondary Coordinator", "coord_senior_sec"),
                ("Pre-primary Coordinator", "coord_pre_primary"),
                ("Principal", "principal")
            ]
            
            sig_files = {}
            personnel_names = {}
            
            for title, key_prefix in coord_titles:
                st.write(f"**{title}**")
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    personnel_names[key_prefix] = st.text_input("Name", value=org_settings.get(f"{key_prefix}_name", ""), key=f"{key_prefix}_name")
                with p_col2:
                    current_sig = org_settings.get(f"{key_prefix}_sig", "")
                    if current_sig:
                        st.image(f"data:image/png;base64,{current_sig}", width=100, caption="Current Signature")
                    sig_files[key_prefix] = st.file_uploader(f"Upload {title} Sign", type=["png", "jpg", "jpeg"], key=f"{key_prefix}_sig_file")
                    
            st.markdown("---")
            save_config_btn = st.form_submit_button("💾 Save Structure Config", type="primary")
            
            if save_config_btn:
                with st.spinner("Saving Settings to Database..."):
                    payload = {
                        "academic_year": ay_val,
                        "academic_year_size": ay_font_size,
                        "academic_year_family": available_fonts.get(ay_font_fam, "helv"),
                        
                        "session_date": sess_val.strftime("%d/%m/%Y") if sess_val else "",
                        "session_size": sess_font_size,
                        "session_family": available_fonts.get(sess_font_fam, "helv"),
                        
                        "time_from": time_from,
                        "time_to": time_to,
                        "time_size": time_font_size,
                        "time_family": available_fonts.get(time_font_fam, "helv")
                    }
                    
                    for key_prefix in personnel_names.keys():
                        payload[f"{key_prefix}_name"] = personnel_names[key_prefix]
                        
                        # Process uploaded signature if any
                        uploaded_sig = sig_files[key_prefix]
                        if uploaded_sig:
                            sig_b64 = base64.b64encode(uploaded_sig.getvalue()).decode()
                            payload[f"{key_prefix}_sig"] = sig_b64
                            
                    up_s_success, up_s_res = update_org_settings(payload)
                    
                if up_s_success:
                    st.success("All structure settings and signatures updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update settings: {up_s_res}")
