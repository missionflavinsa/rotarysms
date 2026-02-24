import pandas as pd

# Define the massive column mapping and reordering for Excel Exports and Imports
EXCEL_COLUMN_MAP = {
    # Form 1: Basic
    'roll_number': 'Roll Number',
    'name': 'Name of the Learner',
    'apaar_id': 'APAAR ID',
    'reg_number': 'Registration No',
    'dob': 'Date of Birth',
    'mother_name': "Mother's Name",
    'father_name': "Father's Name",
    'profile_photo': 'Profile Photo URL',
    'email': 'Email',
    
    # Form 2: Insights
    'ins_grow_up': 'F2: Grow Up To Be',
    'ins_age': 'F2: Age',
    'ins_food': 'F2: Fav Food',
    'ins_game': 'F2: Fav Game',
    'ins_festival': 'F2: Fav Festival',
    'ins_inspire': 'F2: Inspiring Person',
    'ins_idol': 'F2: Idol',
    'ins_learn': 'F2: Want to Learn',
    'ins_improve': 'F2: Improve Skill',
    'ins_like': 'F2: I Like To',
    'ins_dislike': 'F2: I Dont Like To',
    'ins_goodat': 'F2: Good At',
    'ins_notgood': 'F2: Not Good At',
    'ins_about_me': 'F2: About Me',
    'ins_family': 'F2: About Family',
    
    # Form 3: Glims
    'glm_notes': 'F3: Photo Captions',
    
    # Form 4: Physical
    'phy_h1': 'F4: Height 1 (cm)',
    'phy_hd1': 'F4: Height 1 Date',
    'phy_h2': 'F4: Height 2 (cm)',
    'phy_hd2': 'F4: Height 2 Date',
    'phy_w1': 'F4: Weight 1 (kg)',
    'phy_wd1': 'F4: Weight 1 Date',
    'phy_w2': 'F4: Weight 2 (kg)',
    'phy_wd2': 'F4: Weight 2 Date',
    'phy_book': 'F4: Fav Book',
    'phy_dislike': 'F4: Dont Like',
    'phy_people': 'F4: Fav People',
    'phy_cope': 'F4: How I Cope',
    'phy_eat': 'F4: Love to Eat',
    'phy_participate': 'F4: Love to Participate',
    'phy_know': 'F4: Want to Know',
    
    # Form 5: Feelings
    'emo_t1_talk': 'F5 T1: Talk Feeling', 'emo_t1_calm': 'F5 T1: Stay Calm', 'emo_t1_understand': 'F5 T1: Understand Friends', 'emo_t1_better': 'F5 T1: Make Better', 'emo_t1_feel': 'F5 T1: Feel At School',
    'emo_t2_talk': 'F5 T2: Talk Feeling', 'emo_t2_calm': 'F5 T2: Stay Calm', 'emo_t2_understand': 'F5 T2: Understand Friends', 'emo_t2_better': 'F5 T2: Make Better', 'emo_t2_feel': 'F5 T2: Feel At School',
    
    # Form 6: Habits
    'hab_t1_flex': 'F6 T1: Attention', 'hab_t1_ask': 'F6 T1: Asks Qs', 'hab_t1_articulate': 'F6 T1: Articulates', 'hab_t1_mindset': 'F6 T1: Growth Mindset', 'hab_t1_reflect': 'F6 T1: Reflects', 'hab_t1_norms': 'F6 T1: Follows Norms', 'hab_t1_control': 'F6 T1: Self Control',
    'hab_t2_flex': 'F6 T2: Attention', 'hab_t2_ask': 'F6 T2: Asks Qs', 'hab_t2_articulate': 'F6 T2: Articulates', 'hab_t2_mindset': 'F6 T2: Growth Mindset', 'hab_t2_reflect': 'F6 T2: Reflects', 'hab_t2_norms': 'F6 T2: Follows Norms', 'hab_t2_control': 'F6 T2: Self Control'
}

def flatten_student_for_export(student_dict):
    """Flattens nested Firestore dictionary into a flat dictionary suitable for pandas."""
    flat = {}
    
    # Base
    flat['roll_number'] = student_dict.get('roll_number', '')
    flat['name'] = student_dict.get('name', '')
    flat['apaar_id'] = student_dict.get('apaar_id', '')
    flat['reg_number'] = student_dict.get('reg_number', '')
    flat['dob'] = student_dict.get('dob', '')
    flat['mother_name'] = student_dict.get('mother_name', '')
    flat['father_name'] = student_dict.get('father_name', '')
    flat['profile_photo'] = student_dict.get('profile_photo', '')
    flat['email'] = student_dict.get('email', '')
    
    # Insights
    ins = student_dict.get('insights', {})
    for k in ['grow_up', 'age', 'food', 'game', 'festival', 'inspire', 'idol', 'learn', 'improve', 'like', 'dislike', 'goodat', 'notgood', 'about_me', 'family']:
        flat[f'ins_{k}'] = ins.get(k, '')
        
    # Glims
    glm = student_dict.get('glims', {})
    flat['glm_notes'] = glm.get('notes', '')
    
    # Physical
    phy = student_dict.get('physical', {})
    for k in ['h1', 'hd1', 'h2', 'hd2', 'w1', 'wd1', 'w2', 'wd2', 'book', 'dislike', 'people', 'cope', 'eat', 'participate', 'know']:
        flat[f'phy_{k}'] = phy.get(k, '')
        
    # Emotional
    emo = student_dict.get('emotional', {})
    for t in ['t1', 't2']:
        t_data = emo.get(t, {})
        for k in ['talk', 'calm', 'understand', 'better']:
            flat[f'emo_{t}_{k}'] = t_data.get(k, '')
        
        # Safe list to string
        feel_val = t_data.get('feel', [])
        flat[f'emo_{t}_feel'] = ", ".join([str(x) for x in feel_val]) if isinstance(feel_val, list) else str(feel_val)
            
    # Habits
    hab = student_dict.get('habits', {})
    for t in ['t1', 't2']:
        t_data = hab.get(t, {})
        for k in ['flex', 'ask', 'articulate', 'mindset', 'reflect', 'norms', 'control']:
            flat[f'hab_{t}_{k}'] = t_data.get(k, '')
            
    return flat

def process_export_dataframe(df_students):
    """Applies flattening and renaming to the core dataframe."""
    import pandas as pd
    
    flattened_rows = [flatten_student_for_export(row) for row in df_students.to_dict('records')]
    export_df = pd.DataFrame(flattened_rows)
    
    export_df.rename(columns=EXCEL_COLUMN_MAP, inplace=True, errors='ignore')
    
    # Ensure all expected columns exist even if empty
    for col in EXCEL_COLUMN_MAP.values():
        if col not in export_df.columns:
            export_df[col] = ""
            
    # Reorder precisely
    template_cols = list(EXCEL_COLUMN_MAP.values())
    export_df = export_df[template_cols]
    return export_df
