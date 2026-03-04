import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime
import io
import requests
from src.database.firebase_init import get_classes_for_teacher, get_students_by_class, update_student, delete_student, add_subject, get_subjects, update_subject, delete_subject, log_activity, bulk_import_students, update_student_attendance, bulk_import_attendance

def render_teacher_classes(teacher_email):
    st.header("🏫 My Assigned Classes")
    st.write("Manage students and academic subjects.")
    
    success, classes = get_classes_for_teacher(teacher_email)
    
    if success:
        if not classes:
            st.info("You are not assigned as a Class Teacher to any class yet.")
        else:
            # Display classes as horizontal tabs
            class_tabs = st.tabs([f"Class {c.get('class_name')} - {c.get('section')}" for c in classes])
            
            for idx, cls in enumerate(classes):
                with class_tabs[idx]:
                    st.write(f"Management Panel for **Class {cls.get('class_name')}-{cls.get('section')}**")
                    
                    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["👥 Student Roster", "📚 Subjects & Results", "📅 Attendance"])
                    
                    with inner_tab1:
                        st.subheader("Students List")
                        s_success, students = get_students_by_class(cls['id'])
                        
                        if s_success:
                            if not students:
                                st.info("No students enrolled in this class.")
                            else:
                                st_tab1, st_tab2, st_tab3 = st.tabs(["📋 View & Edit", "➕ Add Individual", "📁 Bulk Import"])
                                
                                with st_tab1:
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
                                        file_name=f"Students_Class_{cls.get('class_name')}_{cls.get('section')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        help="Download this class roster as an Excel file, update missing fields, and re-upload via Bulk Import.",
                                        type="secondary",
                                        key=f"export_btn_{cls['id']}"
                                    )
                                    st.write('<div style="height: 15px;"></div>', unsafe_allow_html=True)
                                    # -------------------------------
                                    
                                    st.write("**Manage Student Data**")
                                    with st.container(border=True):
                                        student_options = {f"{s['roll_number']} - {s['name']}": s['id'] for s in students}
                                        student_map = {s['id']: s for s in students}
                                        
                                        selected_student_label = st.selectbox(f"Select Student from {cls['class_name']}-{cls['section']}", options=list(student_options.keys()), key=f"sel_{cls['id']}")
                                        selected_student_id = student_options[selected_student_label]
                                        selected_student_data = student_map[selected_student_id]
                                        
                                        # Full width for update form
                                        with st.container():
                                            with st.form(f"update_student_form_{cls['id']}"):
                                                wiz_t1, wiz_t2, wiz_t3, wiz_t4, wiz_t5, wiz_t6, wiz_t7 = st.tabs([
                                                    "1. Basic", "2. Insight", "3. Glims", 
                                                    "4. Physical", "5. Feelings", "6. Habits", "7. Family"
                                                ])
                                                
                                                ins = selected_student_data.get('insights', {})
                                                phy = selected_student_data.get('physical', {})
                                                glm = selected_student_data.get('glims', {})
                                                emo = selected_student_data.get('emotional', {})
                                                emo_t1 = emo.get('t1', {})
                                                emo_t2 = emo.get('t2', {})
                                                hab = selected_student_data.get('habits', {})
                                                hab_t1 = hab.get('t1', {})
                                                hab_t2 = hab.get('t2', {})
                                                
                                                with wiz_t1:
                                                    st.write("**Form 1: Basic Information**")
                                                    u_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"], key=f"t_u_photo_{cls['id']}")
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
                                                                        from io import BytesIO
                                                                        from PIL import Image, ImageOps
                                                                        img = Image.open(BytesIO(resp.content))
                                                                        img = ImageOps.exif_transpose(img)
                                                                        buf = BytesIO()
                                                                        img.save(buf, format=img.format or "JPEG")
                                                                        st.image(buf.getvalue(), width=100, caption="Current Photo")
                                                                    except Exception:
                                                                        st.caption("Current Photo Error")
                                                                else:
                                                                    st.image(current_photo, width=100, caption="Current Photo")
                                                            else:
                                                                st.image(base64.b64decode(current_photo), width=100, caption="Current Photo")
                                                        except Exception:
                                                            pass
                                                        
                                                    u_name = st.text_input("Name", value=selected_student_data.get('name', ''), key=f"t_u_name_{cls['id']}")
                                                    u_apaar = st.text_input("APAAR ID", value=selected_student_data.get('apaar_id', ''), key=f"t_u_apaar_{cls['id']}")
                                                    u_reg = st.text_input("Reg No", value=selected_student_data.get('reg_number', ''), key=f"t_u_reg_{cls['id']}")
                                                    u_roll = st.text_input("Roll No", value=selected_student_data.get('roll_number', ''), key=f"t_u_roll_{cls['id']}")
                                                    dob_str = selected_student_data.get('dob', '')
                                                    u_dob = st.text_input("DOB (DD/MM/YYYY)", value=dob_str, placeholder="15/08/2010", key=f"t_u_dob_{cls['id']}")
                                                    u_email = st.text_input("Email", value=selected_student_data.get('email', ''), key=f"t_u_email_{cls['id']}")
                                                    u_mother = st.text_input("Mother Name", value=selected_student_data.get('mother_name', ''), key=f"t_u_mother_{cls['id']}")
                                                    u_father = st.text_input("Father Name", value=selected_student_data.get('father_name', ''), key=f"t_u_father_{cls['id']}")

                                                with wiz_t2:
                                                    st.write("**Form 2: Learner's Insight**")
                                                    c2_1, c2_2 = st.columns(2)
                                                    u_f2_grow_up = c2_1.text_input("Grow up to be:", value=ins.get('grow_up', ''), key=f"t_u_f2_1_{cls['id']}")
                                                    u_f2_age = c2_2.text_input("Age:", value=ins.get('age', ''), key=f"t_u_f2_2_{cls['id']}")
                                                    u_f2_food = c2_1.text_input("Fav Food:", value=ins.get('food', ''), key=f"t_u_f2_3_{cls['id']}")
                                                    u_f2_game = c2_2.text_input("Fav Game:", value=ins.get('game', ''), key=f"t_u_f2_4_{cls['id']}")
                                                    u_f2_festival = c2_1.text_input("Fav Festival:", value=ins.get('festival', ''), key=f"t_u_f2_5_{cls['id']}")
                                                    u_f2_inspire = c2_2.text_input("Inspiring Person:", value=ins.get('inspire', ''), key=f"t_u_f2_6_{cls['id']}")
                                                    u_f2_idol = c2_1.text_input("Idol:", value=ins.get('idol', ''), key=f"t_u_f2_7_{cls['id']}")
                                                    u_f2_improve = c2_2.text_input("Improve Skill:", value=ins.get('improve', ''), key=f"t_u_f2_9_{cls['id']}")
                                                    u_f2_like = c2_1.text_input("I Like To:", value=ins.get('like', ''), key=f"t_u_f2_10_{cls['id']}")
                                                    u_f2_dislike = c2_2.text_input("I Don’t Like To:", value=ins.get('dislike', ''), key=f"t_u_f2_11_{cls['id']}")
                                                    u_f2_goodat = c2_1.text_input("Good At:", value=ins.get('goodat', ''), key=f"t_u_f2_12_{cls['id']}")
                                                    u_f2_notgood = c2_2.text_input("Not Good At:", value=ins.get('notgood', ''), key=f"t_u_f2_13_{cls['id']}")
                                                    u_f2_learn = st.text_area("Want to Learn:", value=ins.get('learn', ''), key=f"t_u_f2_8_{cls['id']}")
                                                    u_f2_about = st.text_area("About Me:", value=ins.get('about_me', ''), key=f"t_u_f2_14_{cls['id']}")
                                                    u_f2_family = st.text_area("About Family:", value=ins.get('family', ''), key=f"t_u_f2_15_{cls['id']}")

                                                with wiz_t3:
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
                                                        f_up = c_up1.file_uploader(f"Upload Image {i+1}", type=["png", "jpg", "jpeg"], key=f"t_u_glm_f_{i}_{cls['id']}")
                                                        c_up = c_up2.text_input(f"Caption {i+1}", value=existing_cap, key=f"t_u_glm_c_{i}_{cls['id']}")
                                                        u_f3_gallery.append((f_up, c_up, existing_photo))
                                                        st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)

                                                with wiz_t4:
                                                    st.write("**Form 4: Physical & Preferences**")
                                                    c4_1, c4_2 = st.columns(2)
                                                    u_f4_h1 = c4_1.number_input("H1 (cm)", value=float(phy.get('h1', 0) or 0), key=f"t_u_f4_h1_{cls['id']}")
                                                    u_f4_hd1 = c4_2.text_input("H1 Date", value=phy.get('hd1', ''), key=f"t_u_f4_hd1_{cls['id']}")
                                                    u_f4_h2 = c4_1.number_input("H2 (cm)", value=float(phy.get('h2', 0) or 0), key=f"t_u_f4_h2_{cls['id']}")
                                                    u_f4_hd2 = c4_2.text_input("H2 Date", value=phy.get('hd2', ''), key=f"t_u_f4_hd2_{cls['id']}")
                                                    u_f4_w1 = c4_1.number_input("W1 (kg)", value=float(phy.get('w1', 0) or 0), key=f"t_u_f4_w1_{cls['id']}")
                                                    u_f4_wd1 = c4_2.text_input("W1 Date", value=phy.get('wd1', ''), key=f"t_u_f4_wd1_{cls['id']}")
                                                    u_f4_w2 = c4_1.number_input("W2 (kg)", value=float(phy.get('w2', 0) or 0), key=f"t_u_f4_w2_{cls['id']}")
                                                    u_f4_wd2 = c4_2.text_input("W2 Date", value=phy.get('wd2', ''), key=f"t_u_f4_wd2_{cls['id']}")
                                                    
                                                    u_f4_book = st.text_input("Fav Book/Song:", value=phy.get('book', ''), key=f"t_u_f4_1_{cls['id']}")
                                                    u_f4_dislike = st.text_input("Don't Like:", value=phy.get('dislike', ''), key=f"t_u_f4_2_{cls['id']}")
                                                    u_f4_people = st.text_input("Fav People:", value=phy.get('people', ''), key=f"t_u_f4_3_{cls['id']}")
                                                    u_f4_eat = st.text_input("Love to Eat:", value=phy.get('eat', ''), key=f"t_u_f4_5_{cls['id']}")
                                                    u_f4_participate = st.text_input("Love to Participate:", value=phy.get('participate', ''), key=f"t_u_f4_6_{cls['id']}")
                                                    u_f4_know = st.text_input("Want to Know:", value=phy.get('know', ''), key=f"t_u_f4_7_{cls['id']}")
                                                    u_f4_cope = st.text_area("How I Cope:", value=phy.get('cope', ''), key=f"t_u_f4_4_{cls['id']}")

                                                feel_opts = ["Always", "Sometimes", "Rarely", "Never"]
                                                def safe_idx(opts, val, default=0): return opts.index(val) if val in opts else default
                                                
                                                with wiz_t5:
                                                    st.write("**Form 5: Feelings (Term 1 & 2)**")
                                                    c5_1, c5_2 = st.columns(2)
                                                    u_f5_t1_1 = c5_1.selectbox("T1: Talk about feeling", feel_opts, index=safe_idx(feel_opts, emo_t1.get('talk')), key=f"t_u_f5_t1_1_{cls['id']}")
                                                    u_f5_t1_2 = c5_1.selectbox("T1: Stay calm", feel_opts, index=safe_idx(feel_opts, emo_t1.get('calm')), key=f"t_u_f5_t1_2_{cls['id']}")
                                                    u_f5_t1_3 = c5_1.selectbox("T1: Understand friends", feel_opts, index=safe_idx(feel_opts, emo_t1.get('understand')), key=f"t_u_f5_t1_3_{cls['id']}")
                                                    u_f5_t1_4 = c5_1.selectbox("T1: Make better", feel_opts, index=safe_idx(feel_opts, emo_t1.get('better')), key=f"t_u_f5_t1_4_{cls['id']}")
                                                    
                                                    u_f5_t2_1 = c5_2.selectbox("T2: Talk about feeling", feel_opts, index=safe_idx(feel_opts, emo_t2.get('talk')), key=f"t_u_f5_t2_1_{cls['id']}")
                                                    u_f5_t2_2 = c5_2.selectbox("T2: Stay calm", feel_opts, index=safe_idx(feel_opts, emo_t2.get('calm')), key=f"t_u_f5_t2_2_{cls['id']}")
                                                    u_f5_t2_3 = c5_2.selectbox("T2: Understand friends", feel_opts, index=safe_idx(feel_opts, emo_t2.get('understand')), key=f"t_u_f5_t2_3_{cls['id']}")
                                                    u_f5_t2_4 = c5_2.selectbox("T2: Make better", feel_opts, index=safe_idx(feel_opts, emo_t2.get('better')), key=f"t_u_f5_t2_4_{cls['id']}")

                                                habit_opts = ["Yes", "Sometimes", "Needs Improvement"]
                                                with wiz_t6:
                                                    st.write("**Form 6: Habits (Term 1 & 2)**")
                                                    c6_1, c6_2 = st.columns(2)
                                                    u_f6_t1_1 = c6_1.selectbox("T1: Flex/Attention", habit_opts, index=safe_idx(habit_opts, hab_t1.get('flex')), key=f"t_u_f6_t1_1_{cls['id']}")
                                                    u_f6_t1_2 = c6_1.selectbox("T1: Asks questions", habit_opts, index=safe_idx(habit_opts, hab_t1.get('ask')), key=f"t_u_f6_t1_2_{cls['id']}")
                                                    u_f6_t1_3 = c6_1.selectbox("T1: Articulates", habit_opts, index=safe_idx(habit_opts, hab_t1.get('articulate')), key=f"t_u_f6_t1_3_{cls['id']}")
                                                    u_f6_t1_4 = c6_1.selectbox("T1: Growth mindset", habit_opts, index=safe_idx(habit_opts, hab_t1.get('mindset')), key=f"t_u_f6_t1_4_{cls['id']}")
                                                    u_f6_t1_5 = c6_1.selectbox("T1: Reflects", habit_opts, index=safe_idx(habit_opts, hab_t1.get('reflect')), key=f"t_u_f6_t1_5_{cls['id']}")
                                                    u_f6_t1_6 = c6_1.selectbox("T1: Follows norms", habit_opts, index=safe_idx(habit_opts, hab_t1.get('norms')), key=f"t_u_f6_t1_6_{cls['id']}")
                                                    u_f6_t1_7 = c6_1.selectbox("T1: Self-control", habit_opts, index=safe_idx(habit_opts, hab_t1.get('control')), key=f"t_u_f6_t1_7_{cls['id']}")
                                                    
                                                    u_f6_t2_1 = c6_2.selectbox("T2: Flex/Attention", habit_opts, index=safe_idx(habit_opts, hab_t2.get('flex')), key=f"t_u_f6_t2_1_{cls['id']}")
                                                    u_f6_t2_2 = c6_2.selectbox("T2: Asks questions", habit_opts, index=safe_idx(habit_opts, hab_t2.get('ask')), key=f"t_u_f6_t2_2_{cls['id']}")
                                                    u_f6_t2_3 = c6_2.selectbox("T2: Articulates", habit_opts, index=safe_idx(habit_opts, hab_t2.get('articulate')), key=f"t_u_f6_t2_3_{cls['id']}")
                                                    u_f6_t2_4 = c6_2.selectbox("T2: Growth mindset", habit_opts, index=safe_idx(habit_opts, hab_t2.get('mindset')), key=f"t_u_f6_t2_4_{cls['id']}")
                                                    u_f6_t2_5 = c6_2.selectbox("T2: Reflects", habit_opts, index=safe_idx(habit_opts, hab_t2.get('reflect')), key=f"t_u_f6_t2_5_{cls['id']}")
                                                    u_f6_t2_6 = c6_2.selectbox("T2: Follows norms", habit_opts, index=safe_idx(habit_opts, hab_t2.get('norms')), key=f"t_u_f6_t2_6_{cls['id']}")
                                                    u_f6_t2_7 = c6_2.selectbox("T2: Self-control", habit_opts, index=safe_idx(habit_opts, hab_t2.get('control')), key=f"t_u_f6_t2_7_{cls['id']}")
                                                    
                                                with wiz_t7:
                                                    st.write("**Form 7: My Family**")
                                                    fam_info = selected_student_data.get('family', {})
                                                    fam_photo = fam_info.get("photo", "")
                                                    if fam_photo:
                                                        st.image(fam_photo, width=200)
                                                    u_fam_f = st.file_uploader("Upload Family Photo", type=["png", "jpg", "jpeg"], key=f"t_u_fam_f_{cls['id']}")
                                                    u_fam_c = st.text_area("About My Family:", value=fam_info.get("desc", ""), key=f"t_u_fam_c_{cls['id']}")
                                                    
                                                st.write('<div style="height: 10px;"></div>', unsafe_allow_html=True)
                                                upd_btn = st.form_submit_button("💾 Save Profile Updates", type="primary")
                                                
                                                if upd_btn:
                                                    if not u_roll or not u_name:
                                                        st.error("Roll Number and Name are required.")
                                                    elif u_dob and not re.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/\d{4}$", u_dob):
                                                        st.error("Date of Birth must be in DD/MM/YYYY format.")
                                                    else:
                                                        with st.spinner("Updating student profile..."):
                                                            photo_val = current_photo
                                                            if u_photo:
                                                                from src.utils.image_utils import process_uploaded_image
                                                                photo_val = process_uploaded_image(u_photo)
                                                            
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
                                                                    from src.utils.image_utils import process_uploaded_image
                                                                    final_photo = "base64," + process_uploaded_image(f_up)
                                                                if final_photo or c_up:
                                                                    p_gl.append({"photo": final_photo, "caption": c_up})
                                                                    
                                                            p_fam = {
                                                                "photo": fam_photo,
                                                                "desc": u_fam_c
                                                            }
                                                            if u_fam_f:
                                                                from src.utils.image_utils import process_uploaded_image
                                                                p_fam["photo"] = "base64," + process_uploaded_image(u_fam_f)

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
                                                            log_activity(teacher_email, "Updated Student", f"{cls.get('class_name')}-{cls.get('section')}", f"Roll: {u_roll}, Name: {u_name}")
                                                            st.success("Successfully updated student.")
                                                            st.rerun()
                                                        else:
                                                            st.error(f"Failed to update: {up_res}")
                                                            
                                        st.write('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                                        with st.expander("🗑️ Danger Zone - Delete Student", expanded=False):
                                            with st.form(f"delete_student_form_{cls['id']}"):
                                                st.warning("This action cannot be undone. All student data will be permanently removed.")
                                                del_btn = st.form_submit_button("Delete Student", type="primary")
                                                
                                                if del_btn:
                                                    with st.spinner("Deleting student..."):
                                                        del_success, del_res = delete_student(selected_student_id)
                                                    if del_success:
                                                        log_activity(teacher_email, "Deleted Student", f"{cls.get('class_name')}-{cls.get('section')}", f"Roll: {selected_student_data.get('roll_number')}")
                                                        st.success("Successfully deleted student.")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"Failed to delete: {del_res}")
                                                        
                                with st_tab2:
                                    st.info("Please ask an Administrator to add individual students manually.")
                                    # Form logic hidden for teachers to match req, or they can use bulk upload.
                                    
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
                                    
                                    with st.expander("ℹ️ How to format F3: Glims Gallery JSON"):
                                        st.markdown("""
                                        If you want to import Glims Gallery photos in bulk, the `F3: Glims Gallery JSON` column must contain a valid JSON array of objects.
                                        
                                        **Example Format:**
                                        ```json
                                        [
                                            {"photo": "https://drive.google.com/...", "caption": "Playing Sports"},
                                            {"photo": "https://drive.google.com/...", "caption": "Reading a Book"}
                                        ]
                                        ```
                                        """)
                                    
                                    st.download_button(
                                        label="📥 Download Sample Bulk Template (CSV)",
                                        data=sample_csv,
                                        file_name="rotary_rms_bulk_student_template.csv",
                                        mime="text/csv",
                                        key=f"dl_csv_{cls['id']}"
                                    )
                                    
                                    st.write("---")
                                    uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["xlsx", "xls", "csv"], key=f"up_{cls['id']}")
                                    
                                    if uploaded_file is not None:
                                        try:
                                            if uploaded_file.name.endswith('.csv'):
                                                df = pd.read_csv(uploaded_file)
                                            else:
                                                df = pd.read_excel(uploaded_file)
                                                
                                            st.dataframe(df.head(), use_container_width=True)
                                            
                                            if st.button("Confirm Import", type="primary", key=f"conf_{cls['id']}"):
                                                with st.spinner("Importing students..."):
                                                    from src.database.firebase_init import bulk_import_students
                                                    imp_success, imp_result = bulk_import_students(cls['id'], df)
                                                if imp_success:
                                                    log_activity(teacher_email, "Bulk Imported Students", f"{cls.get('class_name')}-{cls.get('section')}")
                                                    st.success(imp_result)
                                                else:
                                                    st.error(imp_result)
                                        except Exception as e:
                                            st.error(f"Error reading file: {e}")

                                    st.write("---")
                                    st.subheader("⚠️ Danger Zone")
                                    st.warning("Deleting all students will permanently remove their profiles, marks, and insights from this class.")
                                    delete_confirm = st.checkbox("I understand the consequences, unlock delete button", key=f"del_conf_{cls['id']}")
                                    if delete_confirm:
                                        if st.button(f"🗑️ Delete ALL Students in {cls.get('class_name')} {cls.get('section')}", type="primary", key=f"del_all_{cls['id']}"):
                                            with st.spinner("Deleting all students..."):
                                                from src.database.firebase_init import delete_all_students_in_class
                                                del_success, del_res = delete_all_students_in_class(cls['id'])
                                            if del_success:
                                                log_activity(teacher_email, "Deleted All Students", f"{cls.get('class_name')}-{cls.get('section')}")
                                                st.success(del_res)
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to delete students: {del_res}")
                        else:
                            st.error(f"Failed to load students: {students}")
                            
                    with inner_tab2:
                        st.subheader("📚 Subject Management & Results")
                        
                        # 1. Subject Creation
                        st.write("**➕ Add New Subject**")
                        with st.container(border=True):
                            with st.form(f"add_sub_form_{cls['id']}"):
                                new_sub_name = st.text_input("Subject Name", placeholder="e.g. Mathematics, Science")
                                add_sub_btn = st.form_submit_button("Create Subject", type="primary")
                                
                                if add_sub_btn:
                                    if not new_sub_name:
                                        st.error("Please enter a subject name.")
                                    else:
                                        with st.spinner("Creating subject..."):
                                            add_s_success, add_s_res = add_subject(cls['id'], new_sub_name)
                                        if add_s_success:
                                            log_activity(teacher_email, "Created Subject", f"{cls.get('class_name')}-{cls.get('section')}", f"Added Subject: {new_sub_name}")
                                            st.success("Subject created!")
                                            st.rerun()
                                        else:
                                            st.error(add_s_res)
                        
                        # 2. List Subjects & Manage Results
                        sub_success, subjects = get_subjects(cls['id'])
                        if sub_success:
                            if not subjects:
                                st.info("No subjects created yet for this class.")
                            else:
                                st.write("**Manage Subject Results**")
                                # Create a tab for each subject
                                sub_tabs = st.tabs([sub['name'] for sub in subjects])
                                
                                for s_idx, sub in enumerate(subjects):
                                    with sub_tabs[s_idx]:
                                        c_col1, c_col2 = st.columns([5, 1])
                                        with c_col1:
                                            st.info("Paste the public Google Sheet link uniquely for this subject.")
                                        with c_col2:
                                            if st.button("🗑️ Delete Form", key=f"del_sub_{sub['id']}", type="secondary", help="Delete this subject entirely"):
                                                with st.spinner("Deleting..."):
                                                    delete_subject(sub['id'])
                                                    log_activity(teacher_email, "Deleted Subject", f"{cls.get('class_name')}-{cls.get('section')}", f"Removed Subject: {sub.get('name')}")
                                                st.rerun()
                                                    
                                        # Form to update/save the URLs
                                        with st.form(f"upd_url_form_{sub['id']}"):
                                            t1_col, t2_col = st.columns(2)
                                            with t1_col:
                                                url_t1 = st.text_input("Term 1 Sheet URL", value=sub.get('sheet_url_t1', ''), placeholder="https://docs.google.com/spreadsheets/d/...")
                                            with t2_col:
                                                url_t2 = st.text_input("Term 2 Sheet URL", value=sub.get('sheet_url_t2', ''), placeholder="https://docs.google.com/spreadsheets/d/...")
                                                
                                            save_url_btn = st.form_submit_button("Save Sheet URLs", use_container_width=True)
                                            if save_url_btn:
                                                with st.spinner("Saving URLs..."):
                                                    update_subject(sub['id'], sheet_url_t1=url_t1, sheet_url_t2=url_t2)
                                                    log_activity(teacher_email, "Saved Sheet URLs", f"{cls.get('class_name')}-{cls.get('section')}", f"Subject: {sub.get('name')}")
                                                st.success("URLs Saved!")
                                                st.rerun()
                                        
                                        # Fetching Logic for both terms
                                        term_tabs = st.tabs(["Term 1 Data", "Term 2 Data"])
                                        
                                        for t_idx, t_name in enumerate(["Term 1", "Term 2"]):
                                            with term_tabs[t_idx]:
                                                term_key = 'sheet_url_t1' if t_idx == 0 else 'sheet_url_t2'
                                                saved_url = sub.get(term_key, '')
                                                
                                                if saved_url:
                                                    try:
                                                        if "/d/" in saved_url:
                                                            doc_id = saved_url.split("/d/")[1].split("/")[0]
                                                            export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                                                            
                                                            cache_key = f"db_tabs_{sub['id']}_{t_idx}_{doc_id}"
                                                            if cache_key not in st.session_state:
                                                                st.session_state[cache_key] = None
                                                                
                                                            col_fetch, col_clear = st.columns([2, 1])
                                                            with col_fetch:
                                                                if st.button(f"Fetch {t_name} Tabs", type="primary", key=f"fetch_tabs_{sub['id']}_{t_idx}"):
                                                                    with st.spinner(f"Downloading {t_name}..."):
                                                                        try:
                                                                            raw_dict = pd.read_excel(export_url, sheet_name=None)
                                                                            clean_dict = {}
                                                                            for s_name, df in raw_dict.items():
                                                                                clean_dict[s_name] = df.fillna("").astype(str)
                                                                            st.session_state[cache_key] = clean_dict
                                                                            st.success("Successfully fetched workbook!")
                                                                            st.rerun()
                                                                        except Exception as e:
                                                                            st.error(f"Error accessing sheet data: {e} - Check link permissions.")
                                                            with col_clear:
                                                                if st.session_state[cache_key] is not None:
                                                                    if st.button("Clear Data", key=f"clear_tabs_{sub['id']}_{t_idx}"):
                                                                        st.session_state[cache_key] = None
                                                                        st.rerun()
                                                                        
                                                            if st.session_state[cache_key] is not None:
                                                                workbook_dict = st.session_state[cache_key]
                                                                tab_names = list(workbook_dict.keys())
                                                                
                                                                selected_tab = st.selectbox(f"Select Target Tab to View ({t_name})", options=tab_names, key=f"sel_tab_{sub['id']}_{t_idx}")
                                                                if selected_tab:
                                                                    df_results = workbook_dict[selected_tab]
                                                                    if df_results.empty:
                                                                        st.warning(f"The tab '{selected_tab}' appears to be empty.")
                                                                    else:
                                                                        st.dataframe(df_results, hide_index=True, use_container_width=True)
                                                        else:
                                                            st.warning("Invalid Google Sheet URL format. Please paste the full URL containing '/d/...'.")
                                                    except Exception as main_e:
                                                        st.error(f"An unexpected error occurred: {main_e}")
                                                else:
                                                    st.info(f"Please save a Google Sheet URL for {t_name} above to fetch data.")
                        else:
                            st.error("Failed to load subjects.")
                            
                    with inner_tab3:
                        st.subheader("📅 Manage Class Attendance (Month-wise)")
                        st.write("Track monthly attendance for individual students or upload bulk data.")
                        
                        months_list = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
                        
                        if not s_success or not students:
                            st.warning("No students found in this class. Please add students first.")
                        else:
                            # 1. Manual Entry Form
                            with st.expander("✍️ Manual Attendance Entry", expanded=True):
                                with st.form(f"t_manual_attendance_form_{cls['id']}"):
                                    col_m, col_s = st.columns(2)
                                    with col_m:
                                        sel_month = st.selectbox("Select Month", options=months_list)
                                    with col_s:
                                        student_opts = {f"{s.get('roll_number', 'N/A')} - {s.get('name', 'Unknown')}": s['id'] for s in students}
                                        sel_student_label = st.selectbox("Select Student", options=list(student_opts.keys()))
                                        sel_student_id = student_opts[sel_student_label]
                                        
                                    col_w, col_a = st.columns(2)
                                    with col_w:
                                        work_days = st.number_input("No. of Working Days", min_value=0, max_value=31, value=20)
                                    with col_a:
                                        att_days = st.number_input("No. of Days Attended", min_value=0, max_value=31, value=20)
                                        
                                    if st.form_submit_button("Save Attendance", type="primary"):
                                        if att_days > work_days:
                                            st.error("Attended days cannot exceed working days.")
                                        else:
                                            with st.spinner("Saving..."):
                                                a_succ, a_res = update_student_attendance(sel_student_id, sel_month, work_days, att_days)
                                            if a_succ:
                                                st.success("Attendance saved successfully!")
                                            else:
                                                st.error(f"Failed to save: {a_res}")

                            # 2. Bulk Upload Form
                            st.write("---")
                            st.write("**📁 Bulk Excel Attendance Upload**")
                            st.info("Upload an Excel file where each sheet represents a month (e.g., April, May).")
                            
                            # Generate Template
                            sample_buffer = io.BytesIO()
                            with pd.ExcelWriter(sample_buffer, engine='openpyxl') as writer:
                                df_template = pd.DataFrame([{
                                    'Roll Number': s.get('roll_number', ''),
                                    'Name of the Learner': s.get('name', ''),
                                    'No. of working days': 20,
                                    'No. of days attended': 20,
                                } for s in students])
                                for m in months_list:
                                    df_template.to_excel(writer, sheet_name=m, index=False)
                            
                            st.download_button(
                                label="📥 Download Class Attendance Template",
                                data=sample_buffer.getvalue(),
                                file_name=f"Attendance_Template_{cls.get('class_name')}_{cls.get('section')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"t_att_dl_{cls['id']}"
                            )
                            
                            att_file = st.file_uploader("Upload filled Attendance Excel", type=["xlsx"], key=f"t_att_up_{cls['id']}")
                            if att_file:
                                try:
                                    wb_dict = pd.read_excel(att_file, sheet_name=None)
                                    st.write(f"Detected {len(wb_dict)} month sheets: {', '.join(list(wb_dict.keys()))}")
                                    
                                    if st.button("🚀 Process Bulk Attendance", type="primary", key=f"t_att_proc_{cls['id']}"):
                                        with st.spinner("Processing workbook across all students..."):
                                            b_succ, b_res = bulk_import_attendance(cls['id'], wb_dict)
                                        if b_succ:
                                            st.success(b_res)
                                            st.rerun()
                                        else:
                                            st.error(b_res)
                                except Exception as e:
                                    st.error(f"Failed to read Excel file: {e}")
                                    
                            # 3. View Attendance
                            st.write("---")
                            with st.expander("👀 View Student Attendance", expanded=False):
                                view_student_opts = {f"{s.get('roll_number', 'N/A')} - {s.get('name', 'Unknown')}": s for s in students}
                                v_sel_student_label = st.selectbox("Select Student to View", options=list(view_student_opts.keys()), key=f"t_view_att_{cls['id']}")
                                v_student_data = view_student_opts[v_sel_student_label]
                                
                                attendance_data = v_student_data.get('attendance', {})
                                if not attendance_data:
                                    st.info("No attendance records found for this student.")
                                else:
                                    att_records = []
                                    for m in months_list:
                                        if m in attendance_data:
                                            att_records.append({
                                                "Month": m,
                                                "Working Days": attendance_data[m].get("working_days", 0),
                                                "Attended Days": attendance_data[m].get("attended_days", 0),
                                                "Percentage (%)": attendance_data[m].get("percentage", 0)
                                            })
                                    if not att_records:
                                        st.info("No attendance records found for this student.")
                                    else:
                                        df_att = pd.DataFrame(att_records)
                                        st.dataframe(df_att, hide_index=True, use_container_width=True)
                                        
    else:
        st.error(f"Failed to load your assigned classes: {classes}")
