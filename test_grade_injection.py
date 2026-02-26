import os
import json
import pandas as pd
from src.views.admin_results import fetch_class_academic_data, generate_report_card

print("Fetching data...")
sub_data = fetch_class_academic_data("H1F8tYtE3zGqIuP4C882")
print("Subjects fetched:", list(sub_data.keys()))

student_data = {
    'id': 'test1',
    'name': 'Aaradhya Prashant Ambede',
    'roll_number': '1'
}

class_data = {
    'class_name': '3',
    'section': 'A'
}

print("Simulating generate_report_card...")
# We will just run the logic inside generate_report_card directly here to see prints
import fitz
doc = fitz.open("tempalates/Progress 3rd to 5th 2026.pdf")

student_name_norm = str(student_data.get('name', '')).lower().strip().replace("  ", " ")
student_roll_norm = str(student_data.get('roll_number', '')).strip()
if student_roll_norm.endswith(".0"):
    student_roll_norm = student_roll_norm[:-2]

print(f"Student Norms - Name: '{student_name_norm}', Roll: '{student_roll_norm}'")

for p_idx in range(4, 10):
    p = doc[p_idx]
    page_text = p.get_text("text").lower().replace('\n', ' ')
    
    # Find which user-defined subject this template page belongs to
    matched_sub = None
    for s_name in sub_data.keys():
        if s_name.lower().strip() in page_text:
            matched_sub = s_name
            break
            
    if matched_sub:
        print(f"\n--- Page {p_idx+1} Matched Subject: {matched_sub} ---")
        term1_df = sub_data[matched_sub].get("t1")
        if term1_df is not None:
            print(f"Term 1 DF columns: {term1_df.columns.tolist()[:5]}...")
            s_row = None
            for _, row in term1_df.iterrows():
                sheet_roll = str(row.values[0]).strip()
                if sheet_roll.endswith(".0"):
                    sheet_roll = sheet_roll[:-2]
                    
                sheet_name = str(row.values[1]).lower().strip().replace("  ", " ")
                
                if (student_roll_norm and sheet_roll == student_roll_norm) or \
                   (student_name_norm and (student_name_norm in sheet_name or sheet_name in student_name_norm)):
                    s_row = row
                    break
            
            if s_row is not None:
                print(f"Found T1 Student Row! Roll: {s_row['ROLL']}, Name: {s_row['NAME']}")
                # check grades
                for cg_code in ['C1.1', 'C1.2']:
                    if cg_code in term1_df.columns:
                        grade = str(s_row[cg_code]).strip()
                        print(f"  T1 Grade for {cg_code}: '{grade}'")
            else:
                print("FAILED to find T1 student row.")
    else:
        print(f"\n--- Page {p_idx+1}: NO MATCHED SUBJECT! ---")
    
