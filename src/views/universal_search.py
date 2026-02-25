import streamlit as st
from src.database.firebase_init import get_all_users, get_all_classes, get_students_by_class, get_classes_for_teacher

def render_universal_search():
    search_options = []
    option_map = {}
    
    # 1. Gather all searchable entities based on User Role
    if st.session_state.user_role == 'admin':
        # Add Pages
        pages = [
            ("📊 Dashboard", "Dashboard"),
            ("👥 Teachers", "Manage Teachers"),
            ("🏫 Classes", "Manage Classes"),
            ("👨‍🎓 Students", "Manage Students"),
            ("📄 Result Generation", "Manage Results"),
            ("⚙️ Settings", "Settings")
        ]
        for p_val, desc in pages:
            label = f"📁 [Page] {desc}"
            search_options.append(label)
            option_map[label] = {"type": "page", "value": p_val, "role": "admin"}
            
        # Add Teachers
        t_success, teachers = get_all_users()
        if t_success and teachers:
            for t in teachers:
                label = f"🧑‍🏫 [Teacher] {t.get('name', 'N/A')} ({t.get('email')})"
                search_options.append(label)
                option_map[label] = {"type": "teacher", "value": t}
                
        # Add Classes & Students
        c_success, classes = get_all_classes()
        if c_success and classes:
            for c in classes:
                clabel = f"🏫 [Class] {c.get('class_name')} - {c.get('section')}"
                search_options.append(clabel)
                option_map[clabel] = {"type": "class", "value": c}
                
                s_success, students = get_students_by_class(c['id'])
                if s_success and students:
                    for s in students:
                        slabel = f"🎓 [Student] {s.get('name')} (Roll: {s.get('roll_number')}) - Class {c.get('class_name')}-{c.get('section')}"
                        search_options.append(slabel)
                        option_map[slabel] = {"type": "student", "class_id": c['id'], "student_id": s['id'], "class_label": clabel}

    elif st.session_state.user_role == 'teacher':
        pages = [
            ("📊 Dashboard", "Dashboard"), 
            ("🏫 My Classes", "My Classes"), 
            ("📄 Result Generation", "Manage Results"), 
            ("⚙️ Settings", "Settings")
        ]
        for p_val, desc in pages:
            label = f"📁 [Page] {desc}"
            search_options.append(label)
            option_map[label] = {"type": "page", "value": p_val, "role": "teacher"}
            
        c_success, classes = get_classes_for_teacher(st.session_state.user_email)
        if c_success and classes:
            for c in classes:
                clabel = f"🏫 [Class] {c.get('class_name')} - {c.get('section')}"
                search_options.append(clabel)
                option_map[clabel] = {"type": "class", "value": c}
                
                s_success, students = get_students_by_class(c['id'])
                if s_success and students:
                    for s in students:
                        slabel = f"🎓 [Student] {s.get('name')} (Roll: {s.get('roll_number')}) - Class {c.get('class_name')}-{c.get('section')}"
                        search_options.append(slabel)
                        option_map[slabel] = {"type": "student", "class_id": c['id'], "student_id": s['id'], "class_label": clabel}

    # 2. Render the Search Bar
    # Use a dummy text to trick the selectbox placeholder
    selected = st.sidebar.selectbox(
        "🔍 Universal Search", 
        options=[""] + search_options, 
        index=0, 
        format_func=lambda x: "Search pages, students, classes..." if x == "" else x,
        help="Type to quickly jump across the entire application!"
    )
    
    # 3. Handle Selection Routing
    if selected and selected != "":
        data = option_map[selected]
        
        # Route Pages
        if data['type'] == 'page':
            if data['role'] == 'admin':
                st.session_state.admin_nav = data['value']
            else:
                st.session_state.teacher_nav = data['value']
                
        # Route Teacher (Admin only)
        elif data['type'] == 'teacher':
            st.session_state.admin_nav = "👥 Teachers"
            st.session_state.search_target_teacher = data['value']['email']
            
        # Route Class
        elif data['type'] == 'class':
            if st.session_state.user_role == 'admin':
                st.session_state.admin_nav = "🏫 Classes"
            else:
                st.session_state.teacher_nav = "🏫 My Classes"
            st.session_state.search_target_class = data['value']['id']
            
        # Route Student
        elif data['type'] == 'student':
            if st.session_state.user_role == 'admin':
                st.session_state.admin_nav = "👨‍🎓 Students"
            else:
                st.session_state.teacher_nav = "🏫 My Classes"
            st.session_state.search_target_class = data['class_id']
            st.session_state.search_target_student = data['student_id']

        # Clear the selectbox selection by forcing a rerun 
        # But wait, without manipulating the key of the selectbox, we can't easily clear it.
        # Streamlit doesn't support 'clearing' a box inherently without query-params or key-change.
        # But since we change page nav, we just rerun.
        st.session_state.trigger_rerun = True
        
    if st.session_state.get('trigger_rerun'):
        st.session_state.trigger_rerun = False
        st.rerun()
