import streamlit as st
import pandas as pd
import base64
from datetime import datetime
import io # Added import for io
import requests
import re # Added import for re, as it's used later for DOB validation
from src.database.firebase_init import (get_all_classes, add_student, bulk_import_students, 
                                        get_students_by_class, update_student, delete_student, get_all_users)

def render_students():
    st.header("👨‍🎓 Student Management")
    st.write("Manage student records and class assignments.")
    
    c_success, classes_list = get_all_classes()
    t_success, users_list = get_all_users()
    
    # Create mapping of email to Name (Email)
    teacher_name_map = {}
    if t_success and users_list:
        for u in users_list:
            teacher_name_map[u['email']] = f"{u.get('name', '')} ({u['email']})" if u.get('name') else u['email']
    
    if not c_success or not classes_list:
        st.warning("You must create at least one class before adding students.")
    else:
        class_options = {f"Class {c['class_name']} - Section {c['section']}": c['id'] for c in classes_list}
        class_map = {c['id']: c for c in classes_list}
        selected_class_label = st.selectbox("Select Target Class:", options=list(class_options.keys()))
        selected_class_id = class_options[selected_class_label]
        
        st.markdown("---")
        st_tab1, st_tab2, st_tab3 = st.tabs(["📋 View & Edit", "➕ Add Individual", "📁 Bulk Import"])
        
        with st_tab1:
            s_success, students = get_students_by_class(selected_class_id)
            if s_success:
                if not students:
                    st.info("No students enrolled in this class.")
                else:
                    df_students = pd.DataFrame(students)
                    
                    # --- TABULAR RENDER PORT & EXCEL FEATURE ---
                    from src.utils.excel_utils import process_export_dataframe
                    export_df = process_export_dataframe(df_students)
                    
                    st.dataframe(export_df, hide_index=True, use_container_width=True)
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='Students')
                    
                    st.download_button(
                        label="📥 Export Class to Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"Students_Class_{class_map[selected_class_id].get('class_name')}_{class_map[selected_class_id].get('section')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Download this class roster as an Excel file, update missing fields, and re-upload via Bulk Import.",
                        type="secondary"
                    )
                    st.write('<div style="height: 15px;"></div>', unsafe_allow_html=True)
                    # -------------------------------
                    
                    student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
                    student_map = {s['id']: s for s in students}
                    
                    st.write("**Manage Student Data**")
                    with st.container(border=True):
                        selected_student_label = st.selectbox(f"Select Student", options=list(student_options.keys()), key=f"admin_sel_stu_{selected_class_id}")
                        selected_student_id = student_options[selected_student_label]
                        selected_student_data = student_map[selected_student_id]
                        
                        # Full width for update form
                        with st.container():
                            with st.form(f"admin_update_stu_form"):
                                wiz_u1, wiz_u2, wiz_u3, wiz_u4, wiz_u5, wiz_u6, wiz_u7 = st.tabs([
                                    "1. Basic", "2. Insight", "3. Glims", 
                                    "4. Physical", "5. Feelings", "6. Habits", "7. Family"
                                ])
                                
                                # Helper extractors
                                ins = selected_student_data.get('insights', {})
                                phy = selected_student_data.get('physical', {})
                                glm = selected_student_data.get('glims', {})
                                emo = selected_student_data.get('emotional', {})
                                emo_t1 = emo.get('t1', {})
                                emo_t2 = emo.get('t2', {})
                                hab = selected_student_data.get('habits', {})
                                hab_t1 = hab.get('t1', {})
                                hab_t2 = hab.get('t2', {})
                                
                                with wiz_u1:
                                    st.write("**Form 1: Basic Information**")
                                    u_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"])
                                    current_photo = selected_student_data.get('profile_photo', '')
                                    if current_photo:
                                        try:
                                            if current_photo.startswith('data:image') or current_photo.startswith('base64,'):
                                                raw = current_photo.split(',')[1] if ',' in current_photo else current_photo.replace('base64,', '')
                                                st.image(base64.b64decode(raw), width=100, caption="Current Photo")
                                            elif current_photo.startswith('http'):
                                                if "drive.google.com" in current_photo:
                                                    try:
                                                        resp = requests.get(current_photo, timeout=5)
                                                        st.image(resp.content, width=100, caption="Current Photo")
                                                    except Exception:
                                                        st.markdown(f'<img src="{current_photo}" width="100" style="border-radius: 5px;">', unsafe_allow_html=True)
                                                        st.caption("Current Photo")
                                                else:
                                                    st.image(current_photo, width=100, caption="Current Photo")
                                            else:
                                                st.image(base64.b64decode(current_photo), width=100, caption="Current Photo")
                                        except Exception:
                                            pass
                                            
                                    u_name = st.text_input("Name", value=selected_student_data.get('name', ''))
                                    u_apaar = st.text_input("APAAR ID", value=selected_student_data.get('apaar_id', ''))
                                    u_reg = st.text_input("Reg No", value=selected_student_data.get('reg_number', ''))
                                    u_roll = st.text_input("Roll No", value=selected_student_data.get('roll_number', ''))
                                    dob_str = selected_student_data.get('dob', '')
                                    u_dob = st.text_input("DOB (DD/MM/YYYY)", value=dob_str, placeholder="15/08/2010")
                                    u_email = st.text_input("Email", value=selected_student_data.get('email', ''))
                                    u_mother = st.text_input("Mother Name", value=selected_student_data.get('mother_name', ''))
                                    u_father = st.text_input("Father Name", value=selected_student_data.get('father_name', ''))

                                with wiz_u2:
                                    st.write("**Form 2: Learner's Insight**")
                                    c2_1, c2_2 = st.columns(2)
                                    u_f2_grow_up = c2_1.text_input("Grow up to be:", value=ins.get('grow_up', ''), key="u_f2_1")
                                    u_f2_age = c2_2.text_input("Age:", value=ins.get('age', ''), key="u_f2_2")
                                    u_f2_food = c2_1.text_input("Fav Food:", value=ins.get('food', ''), key="u_f2_3")
                                    u_f2_game = c2_2.text_input("Fav Game:", value=ins.get('game', ''), key="u_f2_4")
                                    u_f2_festival = c2_1.text_input("Fav Festival:", value=ins.get('festival', ''), key="u_f2_5")
                                    u_f2_inspire = c2_2.text_input("Inspiring Person:", value=ins.get('inspire', ''), key="u_f2_6")
                                    u_f2_idol = c2_1.text_input("Idol:", value=ins.get('idol', ''), key="u_f2_7")
                                    u_f2_improve = c2_2.text_input("Improve Skill:", value=ins.get('improve', ''), key="u_f2_9")
                                    u_f2_like = c2_1.text_input("I Like To:", value=ins.get('like', ''), key="u_f2_10")
                                    u_f2_dislike = c2_2.text_input("I Don’t Like To:", value=ins.get('dislike', ''), key="u_f2_11")
                                    u_f2_goodat = c2_1.text_input("Good At:", value=ins.get('goodat', ''), key="u_f2_12")
                                    u_f2_notgood = c2_2.text_input("Not Good At:", value=ins.get('notgood', ''), key="u_f2_13")
                                    u_f2_learn = st.text_area("Want to Learn:", value=ins.get('learn', ''), key="u_f2_8")
                                    u_f2_about = st.text_area("About Me:", value=ins.get('about_me', ''), key="u_f2_14")
                                    u_f2_family = st.text_area("About Family:", value=ins.get('family', ''), key="u_f2_15")

                                with wiz_u3:
                                    st.write("**Form 3: My Glims (Gallery)**")
                                    st.write("Upload up to 5 memory photos with captions.")
                                    glims_list = glm if isinstance(glm, list) else []
                                    u_f3_gallery = []
                                    for i in range(5):
                                        st.markdown(f"**Photo {i+1}**")
                                        existing_photo = glims_list[i].get("photo", "") if i < len(glims_list) else ""
                                        existing_cap = glims_list[i].get("caption", "") if i < len(glims_list) else ""
                                        
                                        if existing_photo:
                                            st.image(existing_photo, width=150)
                                            
                                        c_up1, c_up2 = st.columns(2)
                                        f_up = c_up1.file_uploader(f"Upload Image {i+1}", type=["png", "jpg", "jpeg"], key=f"u_glm_f_{i}_{selected_student_id}")
                                        c_up = c_up2.text_input(f"Caption {i+1}", value=existing_cap, key=f"u_glm_c_{i}_{selected_student_id}")
                                        u_f3_gallery.append((f_up, c_up, existing_photo))
                                        st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)

                                with wiz_u4:
                                    st.write("**Form 4: Physical & Preferences**")
                                    c4_1, c4_2 = st.columns(2)
                                    u_f4_h1 = c4_1.number_input("H1 (cm)", value=float(phy.get('h1', 0) or 0), key="u_f4_h1")
                                    u_f4_hd1 = c4_2.text_input("H1 Date", value=phy.get('hd1', ''), key="u_f4_hd1")
                                    u_f4_h2 = c4_1.number_input("H2 (cm)", value=float(phy.get('h2', 0) or 0), key="u_f4_h2")
                                    u_f4_hd2 = c4_2.text_input("H2 Date", value=phy.get('hd2', ''), key="u_f4_hd2")
                                    u_f4_w1 = c4_1.number_input("W1 (kg)", value=float(phy.get('w1', 0) or 0), key="u_f4_w1")
                                    u_f4_wd1 = c4_2.text_input("W1 Date", value=phy.get('wd1', ''), key="u_f4_wd1")
                                    u_f4_w2 = c4_1.number_input("W2 (kg)", value=float(phy.get('w2', 0) or 0), key="u_f4_w2")
                                    u_f4_wd2 = c4_2.text_input("W2 Date", value=phy.get('wd2', ''), key="u_f4_wd2")
                                    
                                    u_f4_book = st.text_input("Fav Book/Song:", value=phy.get('book', ''), key="u_f4_1")
                                    u_f4_dislike = st.text_input("Don't Like:", value=phy.get('dislike', ''), key="u_f4_2")
                                    u_f4_people = st.text_input("Fav People:", value=phy.get('people', ''), key="u_f4_3")
                                    u_f4_eat = st.text_input("Love to Eat:", value=phy.get('eat', ''), key="u_f4_5")
                                    u_f4_participate = st.text_input("Love to Participate:", value=phy.get('participate', ''), key="u_f4_6")
                                    u_f4_know = st.text_input("Want to Know:", value=phy.get('know', ''), key="u_f4_7")
                                    u_f4_cope = st.text_area("How I Cope:", value=phy.get('cope', ''), key="u_f4_4")

                                feel_opts = ["Always", "Sometimes", "Rarely", "Never"]
                                def safe_idx(opts, val, default=0): return opts.index(val) if val in opts else default
                                
                                with wiz_u5:
                                    st.write("**Form 5: Feelings (Term 1 & 2)**")
                                    c5_1, c5_2 = st.columns(2)
                                    u_f5_t1_1 = c5_1.selectbox("T1: Talk about feeling", feel_opts, index=safe_idx(feel_opts, emo_t1.get('talk')), key="u_f5_t1_1")
                                    u_f5_t1_2 = c5_1.selectbox("T1: Stay calm", feel_opts, index=safe_idx(feel_opts, emo_t1.get('calm')), key="u_f5_t1_2")
                                    u_f5_t1_3 = c5_1.selectbox("T1: Understand friends", feel_opts, index=safe_idx(feel_opts, emo_t1.get('understand')), key="u_f5_t1_3")
                                    u_f5_t1_4 = c5_1.selectbox("T1: Make better", feel_opts, index=safe_idx(feel_opts, emo_t1.get('better')), key="u_f5_t1_4")
                                    
                                    u_f5_t2_1 = c5_2.selectbox("T2: Talk about feeling", feel_opts, index=safe_idx(feel_opts, emo_t2.get('talk')), key="u_f5_t2_1")
                                    u_f5_t2_2 = c5_2.selectbox("T2: Stay calm", feel_opts, index=safe_idx(feel_opts, emo_t2.get('calm')), key="u_f5_t2_2")
                                    u_f5_t2_3 = c5_2.selectbox("T2: Understand friends", feel_opts, index=safe_idx(feel_opts, emo_t2.get('understand')), key="u_f5_t2_3")
                                    u_f5_t2_4 = c5_2.selectbox("T2: Make better", feel_opts, index=safe_idx(feel_opts, emo_t2.get('better')), key="u_f5_t2_4")

                                habit_opts = ["Yes", "Sometimes", "Needs Improvement"]
                                with wiz_u6:
                                    st.write("**Form 6: Habits (Term 1 & 2)**")
                                    c6_1, c6_2 = st.columns(2)
                                    u_f6_t1_1 = c6_1.selectbox("T1: Flex/Attention", habit_opts, index=safe_idx(habit_opts, hab_t1.get('flex')), key="u_f6_t1_1")
                                    u_f6_t1_2 = c6_1.selectbox("T1: Asks questions", habit_opts, index=safe_idx(habit_opts, hab_t1.get('ask')), key="u_f6_t1_2")
                                    u_f6_t1_3 = c6_1.selectbox("T1: Articulates", habit_opts, index=safe_idx(habit_opts, hab_t1.get('articulate')), key="u_f6_t1_3")
                                    u_f6_t1_4 = c6_1.selectbox("T1: Growth mindset", habit_opts, index=safe_idx(habit_opts, hab_t1.get('mindset')), key="u_f6_t1_4")
                                    u_f6_t1_5 = c6_1.selectbox("T1: Reflects", habit_opts, index=safe_idx(habit_opts, hab_t1.get('reflect')), key="u_f6_t1_5")
                                    u_f6_t1_6 = c6_1.selectbox("T1: Follows norms", habit_opts, index=safe_idx(habit_opts, hab_t1.get('norms')), key="u_f6_t1_6")
                                    u_f6_t1_7 = c6_1.selectbox("T1: Self-control", habit_opts, index=safe_idx(habit_opts, hab_t1.get('control')), key="u_f6_t1_7")
                                    
                                    u_f6_t2_1 = c6_2.selectbox("T2: Flex/Attention", habit_opts, index=safe_idx(habit_opts, hab_t2.get('flex')), key="u_f6_t2_1")
                                    u_f6_t2_2 = c6_2.selectbox("T2: Asks questions", habit_opts, index=safe_idx(habit_opts, hab_t2.get('ask')), key="u_f6_t2_2")
                                    u_f6_t2_3 = c6_2.selectbox("T2: Articulates", habit_opts, index=safe_idx(habit_opts, hab_t2.get('articulate')), key="u_f6_t2_3")
                                    u_f6_t2_4 = c6_2.selectbox("T2: Growth mindset", habit_opts, index=safe_idx(habit_opts, hab_t2.get('mindset')), key="u_f6_t2_4")
                                    u_f6_t2_5 = c6_2.selectbox("T2: Reflects", habit_opts, index=safe_idx(habit_opts, hab_t2.get('reflect')), key="u_f6_t2_5")
                                    u_f6_t2_6 = c6_2.selectbox("T2: Follows norms", habit_opts, index=safe_idx(habit_opts, hab_t2.get('norms')), key="u_f6_t2_6")
                                    u_f6_t2_7 = c6_2.selectbox("T2: Self-control", habit_opts, index=safe_idx(habit_opts, hab_t2.get('control')), key="u_f6_t2_7")
                                    
                                with wiz_u7:
                                    st.write("**Form 7: My Family**")
                                    fam_info = selected_student_data.get('family', {})
                                    fam_photo = fam_info.get("photo", "")
                                    if fam_photo:
                                        st.image(fam_photo, width=200)
                                    u_fam_f = st.file_uploader("Upload Family Photo", type=["png", "jpg", "jpeg"], key=f"u_fam_f_{selected_student_id}")
                                    u_fam_c = st.text_area("About My Family:", value=fam_info.get("desc", ""), key=f"u_fam_c_{selected_student_id}")
                                    
                                st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                                upd_btn = st.form_submit_button("💾 Save Profile Updates")
                                
                                if upd_btn:
                                    if not u_roll or not u_name:
                                        st.error("Roll Number and Name are required.")
                                    elif u_dob and not re.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/\d{4}$", u_dob):
                                        st.error("Date of Birth must be in DD/MM/YYYY format.")
                                    else:
                                        with st.spinner("Updating student profile..."):
                                            photo_val = current_photo
                                            if u_photo:
                                                photo_val = base64.b64encode(u_photo.getvalue()).decode()
                                            
                                            p_ins = {
                                                "grow_up": u_f2_grow_up, "age": u_f2_age, "food": u_f2_food, "game": u_f2_game,
                                                "festival": u_f2_festival, "inspire": u_f2_inspire, "idol": u_f2_idol,
                                                "learn": u_f2_learn, "improve": u_f2_improve, "like": u_f2_like, "dislike": u_f2_dislike,
                                                "goodat": u_f2_goodat, "notgood": u_f2_notgood, "about_me": u_f2_about, "family": u_f2_family
                                            }
                                            p_phy = {
                                                "h1": u_f4_h1, "hd1": u_f4_hd1, "h2": u_f4_h2, "hd2": u_f4_hd2,
                                                "w1": u_f4_w1, "wd1": u_f4_wd1, "w2": u_f4_w2, "wd2": u_f4_wd2,
                                                "book": u_f4_book, "dislike": u_f4_dislike, "people": u_f4_people,
                                                "cope": u_f4_cope, "eat": u_f4_eat, "participate": u_f4_participate, "know": u_f4_know
                                            }
                                            p_gl = []
                                            for f_up, c_up, existing_photo in u_f3_gallery:
                                                final_photo = existing_photo
                                                if f_up:
                                                    final_photo = "base64," + base64.b64encode(f_up.getvalue()).decode()
                                                if final_photo or c_up:
                                                    p_gl.append({"photo": final_photo, "caption": c_up})
                                                    
                                            p_fam = {
                                                "photo": fam_photo,
                                                "desc": u_fam_c
                                            }
                                            if u_fam_f:
                                                p_fam["photo"] = "base64," + base64.b64encode(u_fam_f.getvalue()).decode()

                                            p_emo = {
                                                "t1": {"talk": u_f5_t1_1, "calm": u_f5_t1_2, "understand": u_f5_t1_3, "better": u_f5_t1_4, "feel": emo_t1.get('feel', [])},
                                                "t2": {"talk": u_f5_t2_1, "calm": u_f5_t2_2, "understand": u_f5_t2_3, "better": u_f5_t2_4, "feel": emo_t2.get('feel', [])}
                                            }
                                            p_hab = {
                                                "t1": {"flex": u_f6_t1_1, "ask": u_f6_t1_2, "articulate": u_f6_t1_3, "mindset": u_f6_t1_4, "reflect": u_f6_t1_5, "norms": u_f6_t1_6, "control": u_f6_t1_7},
                                                "t2": {"flex": u_f6_t2_1, "ask": u_f6_t2_2, "articulate": u_f6_t2_3, "mindset": u_f6_t2_4, "reflect": u_f6_t2_5, "norms": u_f6_t2_6, "control": u_f6_t2_7}
                                            }

                                            up_success, up_res = update_student(
                                                selected_student_id, roll_number=u_roll, name=u_name, 
                                                apaar_id=u_apaar, reg_number=u_reg, dob=str(u_dob) if u_dob else "", 
                                                profile_photo=photo_val, email=u_email,
                                                mother_name=u_mother, father_name=u_father,
                                                insights=p_ins, physical=p_phy, glims=p_gl, emotional=p_emo, habits=p_hab, family=p_fam
                                            )
                                        if up_success:
                                            st.success("Successfully updated student.")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update: {up_res}")
                        st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                        with st.expander("🗑️ Danger Zone - Delete Student", expanded=False):
                            with st.form(f"admin_delete_stu_form"):
                                st.warning("This action cannot be undone. All student data will be permanently removed.")
                                del_btn = st.form_submit_button("Delete Student", type="primary")
                                
                                if del_btn:
                                    with st.spinner("Deleting student..."):
                                        del_success, del_res = delete_student(selected_student_id)
                                    if del_success:
                                        st.success("Successfully deleted student.")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {del_res}")
            else:
                st.error(f"Failed to load students: {students}")

        with st_tab2:
            st.subheader("Student Data Wizard")
            st.write("Fill out the sections below. You can navigate between tabs before saving.")
            
            with st.form("add_student_wizard_form"):
                wiz_t1, wiz_t2, wiz_t3, wiz_t4, wiz_t5, wiz_t6, wiz_t7 = st.tabs([
                    "1. Basic Info", "2. Learner's Insight", "3. Glims (Photos)", 
                    "4. Physical & Preferences", "5. Feelings", "6. Habits", "7. Family"
                ])
                
                with wiz_t1:
                    st.write("**Form 1: Basic Information**")
                    n_photo = st.file_uploader("Profile Photo", type=["png", "jpg", "jpeg"])
                    n_name = st.text_input("Name of the Learner")
                    n_apaar = st.text_input("APAAR ID/PEN")
                    n_reg = st.text_input("Registration/Admission Number")
                    n_roll = st.text_input("Roll Number")
                    
                    n_class_id = st.selectbox("Class & Section", options=list(class_options.values()), format_func=lambda x: [k for k,v in class_options.items() if v == x][0], index=list(class_options.values()).index(selected_class_id))
                    n_dob = st.text_input("Date of Birth (DD/MM/YYYY)", placeholder="e.g. 15/08/2010")
                    
                    target_cls_data = class_map.get(n_class_id, {})
                    assigned_teacher = target_cls_data.get('teacher_email', '')
                    default_t_idx = list(teacher_name_map.keys()).index(assigned_teacher) if assigned_teacher in teacher_name_map else 0
                    n_teacher_label = st.selectbox("Class Teacher", options=list(teacher_name_map.values()), index=default_t_idx)
                    
                    n_email = st.text_input("Email (Optional)")
                    n_mother = st.text_input("Name of Mother")
                    n_father = st.text_input("Name of Father")
                    
                with wiz_t2:
                    st.write("**Form 2: Learner's Insight**")
                    st.markdown("##### Basic Personal Reflection")
                    f2_grow_up = st.text_input("When I grow up, I want to be:", key="n_f2_1")
                    f2_age = st.text_input("My Age (in years):", key="n_f2_2")
                    st.markdown("##### My Favorites")
                    f2_food = st.text_input("My Favourite Food:", key="n_f2_3")
                    f2_game = st.text_input("My Favourite Game(s):", key="n_f2_4")
                    f2_festival = st.text_input("My Favourite Festival(s):", key="n_f2_5")
                    f2_inspire = st.text_input("One Person Who Inspires Me:", key="n_f2_6")
                    f2_idol = st.text_input("My Idol:", key="n_f2_7")
                    st.markdown("##### My Learning Goals")
                    f2_learn = st.text_area("Three Things I Want to Learn This Year:", key="n_f2_8")
                    f2_improve = st.text_input("I Would Like to Improve My Skill of:", key="n_f2_9")
                    f2_like = st.text_input("I Like To:", key="n_f2_10")
                    f2_dislike = st.text_input("I Don’t Like To:", key="n_f2_11")
                    st.markdown("##### Self Awareness")
                    f2_goodat = st.text_input("I Am Good At:", key="n_f2_12")
                    f2_notgood = st.text_input("I Am Not So Good At:", key="n_f2_13")
                    f2_about_me = st.text_area("Things About Me (Describe Yourself):", key="n_f2_14")
                    f2_family = st.text_area("About My Family:", key="n_f2_15")
                    
                with wiz_t3:
                    st.write("**Form 3: My Glims (Gallery)**")
                    st.write("Upload up to 5 memory photos with captions.")
                    n_f3_gallery = []
                    for i in range(5):
                        st.markdown(f"**Photo {i+1}**")
                        c_up1, c_up2 = st.columns(2)
                        f_up = c_up1.file_uploader(f"Upload Image {i+1}", type=["png", "jpg", "jpeg"], key=f"n_glm_f_{i}")
                        c_up = c_up2.text_input(f"Caption {i+1}", key=f"n_glm_c_{i}")
                        n_f3_gallery.append((f_up, c_up))
                        st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                    
                with wiz_t4:
                    st.write("**Form 4: All About Me**")
                    st.markdown("##### Physical Growth Tracking")
                    c4_1, c4_2 = st.columns(2)
                    f4_h1 = c4_1.number_input("Height (First Measurement - cm)", key="n_f4_h1")
                    f4_hd1 = c4_2.date_input("Height Measurement Date (First)", key="n_f4_hd1", value=None)
                    f4_h2 = c4_1.number_input("Height (Second Measurement - cm)", key="n_f4_h2")
                    f4_hd2 = c4_2.date_input("Height Measurement Date (Second)", key="n_f4_hd2", value=None)
                    
                    f4_w1 = c4_1.number_input("Weight (First Measurement - kg)", key="n_f4_w1")
                    f4_wd1 = c4_2.date_input("Weight Measurement Date (First)", key="n_f4_wd1", value=None)
                    f4_w2 = c4_1.number_input("Weight (Second Measurement - kg)", key="n_f4_w2")
                    f4_wd2 = c4_2.date_input("Weight Measurement Date (Second)", key="n_f4_wd2", value=None)
                    
                    st.markdown("##### Interests & Preferences")
                    f4_book = st.text_input("My Favourite Book/Poem/Song/Story:", key="n_f4_1")
                    f4_dislike = st.text_input("I Do Not Like:", key="n_f4_2")
                    f4_people = st.text_input("My Favourite People Are:", key="n_f4_3")
                    f4_cope = st.text_area("How Do I Cope When I Face Problems?:", key="n_f4_4")
                    f4_eat = st.text_input("I Love To Eat:", key="n_f4_5")
                    f4_participate = st.text_input("I Love To Participate In:", key="n_f4_6")
                    f4_know = st.text_input("I Want To Know More About:", key="n_f4_7")
                    
                with wiz_t5:
                    st.write("**Form 5: How Do I Feel At School**")
                    feel_opts = ["Always", "Sometimes", "Rarely", "Never"]
                    st.markdown("##### Term 1")
                    f5_t1_1 = st.selectbox("I can talk about how I feel", feel_opts, key="n_f5_t1_1")
                    f5_t1_2 = st.selectbox("In difficult situations, I am able to stay calm", feel_opts, key="n_f5_t1_2")
                    f5_t1_3 = st.selectbox("I understand how my friends feel", feel_opts, key="n_f5_t1_3")
                    f5_t1_4 = st.selectbox("When someone is sad, I can make them feel better", feel_opts, key="n_f5_t1_4")
                    f5_t1_5 = st.multiselect("I Feel at School:", ["Curious", "Happy", "Safe", "Confident", "Excited", "Other"], key="n_f5_t1_5")
                    
                    st.markdown("##### Term 2")
                    f5_t2_1 = st.selectbox("I can talk about how I feel", feel_opts, key="n_f5_t2_1")
                    f5_t2_2 = st.selectbox("In difficult situations, I am able to stay calm", feel_opts, key="n_f5_t2_2")
                    f5_t2_3 = st.selectbox("I understand how my friends feel", feel_opts, key="n_f5_t2_3")
                    f5_t2_4 = st.selectbox("When someone is sad, I can make them feel better", feel_opts, key="n_f5_t2_4")
                    f5_t2_5 = st.multiselect("I Feel at School:", ["Curious", "Happy", "Safe", "Confident", "Excited", "Other"], key="n_f5_t2_5")

                with wiz_t6:
                    st.write("**Form 6: Positive Learning Habits**")
                    habit_opts = ["Yes", "Sometimes", "Needs Improvement"]
                    st.markdown("##### Term 1")
                    f6_t1_1 = st.selectbox("Has the mental flexibility to sustain/shift attention", habit_opts, key="n_f6_t1_1")
                    f6_t1_2 = st.selectbox("Asks interesting and relevant questions", habit_opts, key="n_f6_t1_2")
                    f6_t1_3 = st.selectbox("Can articulate opinions in a coherent manner", habit_opts, key="n_f6_t1_3")
                    f6_t1_4 = st.selectbox("Has growth mindset/seeks help actively", habit_opts, key="n_f6_t1_4")
                    f6_t1_5 = st.selectbox("Reflects on work and takes suitable action", habit_opts, key="n_f6_t1_5")
                    f6_t1_6 = st.selectbox("Follows classroom norms with understanding", habit_opts, key="n_f6_t1_6")
                    f6_t1_7 = st.selectbox("Has self-control that enables learning", habit_opts, key="n_f6_t1_7")
                    
                    st.markdown("##### Term 2")
                    f6_t2_1 = st.selectbox("Has the mental flexibility to sustain/shift attention", habit_opts, key="n_f6_t2_1")
                    f6_t2_2 = st.selectbox("Asks interesting and relevant questions", habit_opts, key="n_f6_t2_2")
                    f6_t2_3 = st.selectbox("Can articulate opinions in a coherent manner", habit_opts, key="n_f6_t2_3")
                    f6_t2_4 = st.selectbox("Has growth mindset/seeks help actively", habit_opts, key="n_f6_t2_4")
                    f6_t2_5 = st.selectbox("Reflects on work and takes suitable action", habit_opts, key="n_f6_t2_5")
                    f6_t2_6 = st.selectbox("Follows classroom norms with understanding", habit_opts, key="n_f6_t2_6")
                    f6_t2_7 = st.selectbox("Has self-control that enables learning", habit_opts, key="n_f6_t2_7")
                    
                with wiz_t7:
                    st.write("**Form 7: My Family**")
                    n_fam_f = st.file_uploader("Upload Family Photo", type=["png", "jpg", "jpeg"], key="n_fam_f")
                    n_fam_c = st.text_area("About My Family:", key="n_fam_c")
                    
                st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                submit_student = st.form_submit_button("💾 Save Entire Student Profile File", type="primary")
                
                if submit_student:
                    if not n_roll or not n_name:
                        st.error("Roll Number and Name (in Tab 1) are required.")
                    elif n_dob and not re.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/\d{4}$", n_dob):
                        st.error("Date of Birth (in Tab 1) must be in DD/MM/YYYY format.")
                    else:
                        with st.spinner("Adding full student profile to database..."):
                            photo_b64 = base64.b64encode(n_photo.getvalue()).decode() if n_photo else ""
                            
                            # Compile sub-dictionaries
                            payload_insights = {
                                "grow_up": f2_grow_up, "age": f2_age, "food": f2_food, "game": f2_game,
                                "festival": f2_festival, "inspire": f2_inspire, "idol": f2_idol,
                                "learn": f2_learn, "improve": f2_improve, "like": f2_like, "dislike": f2_dislike,
                                "goodat": f2_goodat, "notgood": f2_notgood, "about_me": f2_about_me, "family": f2_family
                            }
                            
                            payload_physical = {
                                "h1": f4_h1, "hd1": str(f4_hd1) if f4_hd1 else "",
                                "h2": f4_h2, "hd2": str(f4_hd2) if f4_hd2 else "",
                                "w1": f4_w1, "wd1": str(f4_wd1) if f4_wd1 else "",
                                "w2": f4_w2, "wd2": str(f4_wd2) if f4_wd2 else "",
                                "book": f4_book, "dislike": f4_dislike, "people": f4_people,
                                "cope": f4_cope, "eat": f4_eat, "participate": f4_participate, "know": f4_know
                            }
                            
                            payload_glims = []
                            for f_up, c_up in n_f3_gallery:
                                final_photo = ""
                                if f_up:
                                    final_photo = "base64," + base64.b64encode(f_up.getvalue()).decode()
                                if final_photo or c_up:
                                    payload_glims.append({"photo": final_photo, "caption": c_up})
                                    
                            payload_family = {
                                "photo": "",
                                "desc": n_fam_c
                            }
                            if n_fam_f:
                                payload_family["photo"] = "base64," + base64.b64encode(n_fam_f.getvalue()).decode()
                            
                            payload_emotional = {
                                "t1": {"talk": f5_t1_1, "calm": f5_t1_2, "understand": f5_t1_3, "better": f5_t1_4, "feel": f5_t1_5},
                                "t2": {"talk": f5_t2_1, "calm": f5_t2_2, "understand": f5_t2_3, "better": f5_t2_4, "feel": f5_t2_5}
                            }
                            
                            payload_habits = {
                                "t1": {"flex": f6_t1_1, "ask": f6_t1_2, "articulate": f6_t1_3, "mindset": f6_t1_4, "reflect": f6_t1_5, "norms": f6_t1_6, "control": f6_t1_7},
                                "t2": {"flex": f6_t2_1, "ask": f6_t2_2, "articulate": f6_t2_3, "mindset": f6_t2_4, "reflect": f6_t2_5, "norms": f6_t2_6, "control": f6_t2_7}
                            }
                            
                            s_success, s_result = add_student(
                                class_id=n_class_id, roll_number=n_roll, name=n_name, 
                                apaar_id=n_apaar, reg_number=n_reg, dob=str(n_dob) if n_dob else "", 
                                profile_photo=photo_b64, email=n_email,
                                mother_name=n_mother, father_name=n_father,
                                insights=payload_insights, physical=payload_physical,
                                glims=payload_glims, emotional=payload_emotional, habits=payload_habits, family=payload_family
                            )
                        if s_success:
                            st.success("Successfully added student profile!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add student: {s_result}")
                            
        with st_tab3:
            st.info("The Excel file must contain these exact column headers: `Roll Number` and `Name of the Learner`")
            st.write("Optional columns: `APAAR ID/PEN`, `Registration/Admission Number`, `Date of Birth` (DD/MM/YYYY), `Email`, `Name of Mother`, `Name of Father`, `Profile Photo URL`")
            
            from src.utils.excel_utils import EXCEL_COLUMN_MAP
            # Create sample CSV dynamically from the exact map
            headers = list(EXCEL_COLUMN_MAP.values())
            sample_csv = ",".join(headers) + "\n"
            # Add one dummy row matching the length of headers
            dummy_row = [""] * len(headers)
            dummy_row[0] = "1" # Roll Number
            dummy_row[1] = "John Doe" # Name
            sample_csv += ",".join(dummy_row) + "\n"
            
            st.download_button(
                label="📥 Download Sample Bulk Template (CSV)",
                data=sample_csv,
                file_name="rotary_rms_bulk_student_template.csv",
                mime="text/csv",
            )
            
            st.write("---")
            uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["xlsx", "xls", "csv"])
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                        
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("Confirm Import", type="primary"):
                        with st.spinner("Importing students..."):
                            imp_success, imp_result = bulk_import_students(selected_class_id, df)
                        if imp_success:
                            st.success(imp_result)
                        else:
                            st.error(imp_result)
                except Exception as e:
                    st.error(f"Error reading file: {e}")
