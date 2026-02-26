import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, firestore
import pandas as pd

# Initialize Firebase App
@st.cache_resource
def init_firebase():
    # Pyrebase configuration for client-side Auth
    firebase_config = {
        "apiKey": st.secrets["firebase"]["apiKey"],
        "authDomain": st.secrets["firebase"]["authDomain"],
        "projectId": st.secrets["firebase"]["projectId"],
        "storageBucket": st.secrets["firebase"]["storageBucket"],
        "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
        "appId": st.secrets["firebase"]["appId"],
        "measurementId": st.secrets["firebase"]["measurementId"],
        "databaseURL": st.secrets["firebase"]["databaseURL"]
    }

    try:
        pb = pyrebase.initialize_app(firebase_config)
        pb_auth = pb.auth()
    except Exception as e:
        st.error(f"Error initializing Pyrebase: {e}")
        pb_auth = None

    # Firebase Admin SDK configuration (for creating users)
    if not firebase_admin._apps:
        try:
            cert_dict = {
                "type": st.secrets["firebase_admin"]["type"],
                "project_id": st.secrets["firebase_admin"]["project_id"],
                "private_key_id": st.secrets["firebase_admin"]["private_key_id"],
                "private_key": st.secrets["firebase_admin"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["firebase_admin"]["client_email"],
                "client_id": st.secrets["firebase_admin"]["client_id"],
                "auth_uri": st.secrets["firebase_admin"]["auth_uri"],
                "token_uri": st.secrets["firebase_admin"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase_admin"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase_admin"]["client_x509_cert_url"],
                "universe_domain": st.secrets["firebase_admin"]["universe_domain"],
            }
            cred = credentials.Certificate(cert_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Error initializing Firebase Admin: {e}")

    return pb_auth

def sign_in(email, password):
    pb_auth = init_firebase()
    if pb_auth:
        try:
            user = pb_auth.sign_in_with_email_and_password(email, password)
            return user
        except Exception as e:
            return None
    return None

def create_user(email, password, name="", profile_photo="", signature=""):
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        
        # Store additional metadata in Firestore
        db = firestore.client()
        db.collection('users').document(user.uid).set({
            "email": email,
            "name": name,
            "profile_photo": profile_photo,
            "signature": signature,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        return True, user.uid
    except Exception as e:
        return False, str(e)

def get_all_users():
    try:
        db = firestore.client()
        users = []
        for user in auth.list_users().iterate_all():
            # Basic info from Auth
            user_data = {
                "uid": user.uid,
                "email": user.email,
                "created_at": user.user_metadata.creation_timestamp,
                "name": "",
                "profile_photo": "",
                "signature": ""
            }
            
            # Enrich with Firestore metadata if available
            doc = db.collection('users').document(user.uid).get()
            if doc.exists:
                meta = doc.to_dict()
                user_data["name"] = meta.get("name", "")
                user_data["profile_photo"] = meta.get("profile_photo", "")
                user_data["signature"] = meta.get("signature", "")
                
            users.append(user_data)
        return True, users
    except Exception as e:
        return False, str(e)

def update_user(uid, new_email=None, new_password=None, name=None, profile_photo=None, signature=None):
    try:
        kwargs = {}
        if new_email:
            kwargs["email"] = new_email
        if new_password:
            kwargs["password"] = new_password
        
        if kwargs:
            auth.update_user(uid, **kwargs)
            
        # Update Firestore metadata
        db = firestore.client()
        meta_data = {}
        if new_email: meta_data["email"] = new_email
        if name is not None: meta_data["name"] = name
        if profile_photo is not None: meta_data["profile_photo"] = profile_photo
        if signature is not None: meta_data["signature"] = signature
        
        if meta_data:
            db.collection('users').document(uid).set(meta_data, merge=True)
            
        return True, "User updated successfully"
    except Exception as e:
        return False, str(e)

def delete_user(uid):
    try:
        auth.delete_user(uid)
        
        # Delete Firestore metadata
        db = firestore.client()
        db.collection('users').document(uid).delete()
        
        return True, "User deleted successfully"
    except Exception as e:
        return False, str(e)

def create_class(class_name, section, teacher_email):
    try:
        db = firestore.client()
        _, new_ref = db.collection('classes').add({
            "class_name": class_name,
            "section": section,
            "teacher_email": teacher_email,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, new_ref.id
    except Exception as e:
        return False, str(e)

def get_all_classes():
    try:
        db = firestore.client()
        docs = db.collection('classes').stream()
        classes = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            classes.append(data)
        return True, classes
    except Exception as e:
        return False, str(e)

def get_classes_for_teacher(teacher_email):
    try:
        db = firestore.client()
        docs = db.collection('classes').where(filter=firestore.FieldFilter('teacher_email', '==', teacher_email)).stream()
        classes = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            classes.append(data)
        return True, classes
    except Exception as e:
        return False, str(e)

def update_class(class_id, class_name=None, section=None, teacher_email=None):
    try:
        db = firestore.client()
        ref = db.collection('classes').document(class_id)
        data = {}
        if class_name: data['class_name'] = class_name
        if section: data['section'] = section
        if teacher_email: data['teacher_email'] = teacher_email
        
        if data:
            ref.update(data)
        return True, "Class updated successfully"
    except Exception as e:
        return False, str(e)

def delete_class(class_id):
    try:
        db = firestore.client()
        db.collection('classes').document(class_id).delete()
        
        # Optionally, delete all students in this class
        students = db.collection('students').where(filter=firestore.FieldFilter('class_id', '==', class_id)).stream()
        for doc in students:
            doc.reference.delete()
            
        return True, "Class deleted successfully"
    except Exception as e:
        return False, str(e)

# --- Students ---

def add_student(class_id, roll_number, name, apaar_id="", reg_number="", dob="", profile_photo="", email="", mother_name="", father_name="", 
                insights=None, physical=None, glims=None, emotional=None, habits=None, family=None):
    try:
        db = firestore.client()
        # Check if student with same roll_number exists in this class
        existing = db.collection('students').where(filter=firestore.FieldFilter('class_id', '==', class_id)).where(filter=firestore.FieldFilter('roll_number', '==', roll_number)).limit(1).stream()
        if len(list(existing)) > 0:
            return False, f"Student with roll number {roll_number} already exists in this class."
            
        payload = {
            "class_id": class_id,
            "roll_number": roll_number,
            "name": name,
            "apaar_id": apaar_id,
            "reg_number": reg_number,
            "dob": str(dob) if dob else "",
            "profile_photo": profile_photo,
            "email": email,
            "mother_name": mother_name,
            "father_name": father_name,
            "insights": insights if insights else {},
            "physical": physical if physical else {},
            "glims": glims if glims is not None else [],
            "emotional": emotional if emotional else {},
            "habits": habits if habits else {},
            "family": family if family else {},
            "created_at": firestore.SERVER_TIMESTAMP
        }
        _, new_ref = db.collection('students').add(payload)
        return True, new_ref.id
    except Exception as e:
        return False, str(e)
        
def get_students_by_class(class_id):
    try:
        db = firestore.client()
        docs = db.collection('students').where(filter=firestore.FieldFilter('class_id', '==', class_id)).order_by('roll_number').stream()
        students = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            students.append(data)
        return True, students
    except Exception as e:
        return False, str(e)

def update_student(student_id, roll_number=None, name=None, apaar_id=None, reg_number=None, dob=None, profile_photo=None, 
                   email=None, mother_name=None, father_name=None,
                   insights=None, physical=None, glims=None, emotional=None, habits=None, family=None):
    try:
        db = firestore.client()
        ref = db.collection('students').document(student_id)
        data = {}
        if roll_number is not None: data['roll_number'] = roll_number
        if name is not None: data['name'] = name
        if apaar_id is not None: data['apaar_id'] = apaar_id
        if reg_number is not None: data['reg_number'] = reg_number
        if dob is not None: data['dob'] = str(dob)
        if profile_photo is not None: data['profile_photo'] = profile_photo
        if email is not None: data['email'] = email
        if mother_name is not None: data['mother_name'] = mother_name
        if father_name is not None: data['father_name'] = father_name
        
        if insights is not None: data['insights'] = insights
        if physical is not None: data['physical'] = physical
        if glims is not None: data['glims'] = glims
        if emotional is not None: data['emotional'] = emotional
        if habits is not None: data['habits'] = habits
        if family is not None: data['family'] = family
        
        if data:
            ref.update(data)
        return True, "Student updated successfully"
    except Exception as e:
        return False, str(e)

def delete_student(student_id):
    try:
        db = firestore.client()
        db.collection('students').document(student_id).delete()
        return True, "Student deleted successfully"
    except Exception as e:
        return False, str(e)

def bulk_import_students(class_id, df):
    """
    Expects a pandas DataFrame adhering to EXCEL_COLUMN_MAP headers.
    It will upsert students based on 'Roll Number' in the current class.
    """
    from src.utils.excel_utils import EXCEL_COLUMN_MAP
    import pandas as pd
    import json
    try:
        db = firestore.client()
        batch = db.batch()
        
        has_new_name = 'Name of the Learner' in df.columns
        name_col = 'Name of the Learner' if has_new_name else 'Name'
        roll_col = 'Roll Number'
        
        required_cols = [roll_col, name_col]
        if not all(col in df.columns for col in required_cols):
             return False, f"Excel file must contain at least '{roll_col}' and '{name_col}' columns."
             
        # Reverse map from Excel Column Header -> Internal Key
        rev_map = {v: k for k, v in EXCEL_COLUMN_MAP.items()}
        
        existing_docs = db.collection('students').where(filter=firestore.FieldFilter('class_id', '==', class_id)).stream()
        existing_map = {doc.to_dict().get('roll_number'): doc.id for doc in existing_docs}
        
        counter = 0
        added_count = 0
        updated_count = 0
        
        for index, row in df.iterrows():
            roll_number = str(row[roll_col]).strip()
            name = str(row[name_col]).strip()
            
            if not roll_number or str(roll_number).lower() == 'nan' or not name or str(name).lower() == 'nan':
                continue
            
            # Helper to safely extract from pandas row
            def get_val(col_header):
                if col_header in df.columns and pd.notna(row[col_header]):
                    val = row[col_header]
                    if isinstance(val, str): return val.strip()
                    return val
                return ""
            
            # Base attributes mapped explicitly for validation (like dob)
            apaar_id = str(get_val('APAAR ID'))
            reg_num = str(get_val('Registration No'))
            email = str(get_val('Email'))
            mother = str(get_val("Mother's Name"))
            father = str(get_val("Father's Name"))
            photo_url = str(get_val('Profile Photo URL'))
            
            dob_raw = get_val('Date of Birth')
            dob = ""
            if dob_raw:
                try:
                    parsed_date = pd.to_datetime(dob_raw, dayfirst=True)
                    dob = parsed_date.strftime('%d/%m/%Y')
                except:
                    dob = str(dob_raw).strip()
            
            # Build nested structures using prefixes
            ins_data, phy_data = {}, {}
            emo_dict = {'t1': {}, 't2': {}}
            hab_dict = {'t1': {}, 't2': {}}
            
            for col_header in df.columns:
                internal_key = rev_map.get(col_header)
                if not internal_key: continue
                
                val = get_val(col_header)
                
                if internal_key.startswith('ins_'):
                    ins_data[internal_key.replace('ins_', '')] = val
                elif internal_key.startswith('phy_'):
                    phy_data[internal_key.replace('phy_', '')] = val
            
            # Emotional Arrays Builder Helper
            def get_emo(t, k): return str(get_val(f'F5 {t.upper()}: {k}'))
            emo_data = {
                't1': {'talk': get_emo('t1','Talk Feeling'), 'calm': get_emo('t1','Stay Calm'), 'understand': get_emo('t1','Understand Friends'), 'better': get_emo('t1','Make Better'), 'feel': [x.strip() for x in str(get_val('F5 T1: Feel At School')).split(',') if x.strip()]},
                't2': {'talk': get_emo('t2','Talk Feeling'), 'calm': get_emo('t2','Stay Calm'), 'understand': get_emo('t2','Understand Friends'), 'better': get_emo('t2','Make Better'), 'feel': [x.strip() for x in str(get_val('F5 T2: Feel At School')).split(',') if x.strip()]}
            }
            
            # Habits Array Builder Helper
            def get_hab(t, k): return str(get_val(f'F6 {t.upper()}: {k}'))
            hab_data = {
                't1': {'flex': get_hab('t1','Attention'), 'ask': get_hab('t1','Asks Qs'), 'articulate': get_hab('t1','Articulates'), 'mindset': get_hab('t1','Growth Mindset'), 'reflect': get_hab('t1','Reflects'), 'norms': get_hab('t1','Follows Norms'), 'control': get_hab('t1','Self Control')},
                't2': {'flex': get_hab('t2','Attention'), 'ask': get_hab('t2','Asks Qs'), 'articulate': get_hab('t2','Articulates'), 'mindset': get_hab('t2','Growth Mindset'), 'reflect': get_hab('t2','Reflects'), 'norms': get_hab('t2','Follows Norms'), 'control': get_hab('t2','Self Control')}
            }

            # Family Builder Helper
            fam_data = {
                'photo': str(get_val('F7: Family Photo URL')),
                'desc': str(get_val('F7: Family Desc'))
            }

            # Glims Builder Helper
            glim_str = str(get_val('F3: Glims Gallery JSON'))
            glim_data = []
            try:
                if glim_str:
                    glim_data = json.loads(glim_str)
            except Exception:
                glim_data = []

            student_data = {
                "class_id": class_id,
                "roll_number": roll_number,
                "name": name,
                "apaar_id": apaar_id,
                "reg_number": reg_num,
                "dob": dob,
                "profile_photo": photo_url,
                "email": email,
                "mother_name": mother,
                "father_name": father,
                "insights": ins_data,
                "physical": phy_data,
                "glims": glim_data,
                "emotional": emo_data,
                "habits": hab_data,
                "family": fam_data,
                "updated_at": firestore.SERVER_TIMESTAMP
            }
                
            if roll_number in existing_map:
                ref = db.collection('students').document(existing_map[roll_number])
                batch.update(ref, student_data)
                updated_count += 1
            else:
                student_data["created_at"] = firestore.SERVER_TIMESTAMP
                ref = db.collection('students').document()
                batch.set(ref, student_data)
                added_count += 1
                
            counter += 1
            if counter % 400 == 0:
                batch.commit()
                batch = db.batch()
                
        if counter % 400 != 0:
            batch.commit()
            
        return True, f"Import complete. Added {added_count} new students. Updated {updated_count} existing students."
    except Exception as e:
        return False, str(e)

# ----------------- Subject Management Operations -----------------

def add_subject(class_id, subject_name):
    try:
        db = firestore.client()
        # Check if subject with same name exists for this class
        existing = db.collection('subjects').where(
            filter=firestore.FieldFilter('class_id', '==', class_id)
        ).where(
            filter=firestore.FieldFilter('name', '==', subject_name)
        ).limit(1).stream()
        
        for _ in existing:
            return False, "A subject with this name already exists in this class."
            
        new_ref = db.collection('subjects').document()
        new_ref.set({
            "class_id": class_id,
            "name": subject_name,
            "sheet_url_t1": "", # Term 1
            "sheet_url_t2": "", # Term 2
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "Subject added successfully"
    except Exception as e:
        return False, f"Failed to add subject: {e}"

def get_subjects(class_id):
    try:
        db = firestore.client()
        docs = db.collection('subjects').where(
            filter=firestore.FieldFilter('class_id', '==', class_id)
        ).stream()
        
        subjects = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            subjects.append(data)
            
        # Sort in python to avoid needing a Firestore composite index
        subjects.sort(key=lambda x: x.get('name', '').lower())
        
        return True, subjects
    except Exception as e:
        return False, str(e)

def update_subject(subject_id, name=None, sheet_url_t1=None, sheet_url_t2=None):
    try:
        db = firestore.client()
        ref = db.collection('subjects').document(subject_id)
        data = {}
        if name is not None: data['name'] = name
        if sheet_url_t1 is not None: data['sheet_url_t1'] = sheet_url_t1
        if sheet_url_t2 is not None: data['sheet_url_t2'] = sheet_url_t2
        
        if data:
            ref.update(data)
        return True, "Subject updated successfully"
    except Exception as e:
        return False, str(e)

def delete_subject(subject_id):
    try:
        db = firestore.client()
        db.collection('subjects').document(subject_id).delete()
        return True, "Subject deleted successfully"
    except Exception as e:
        return False, str(e)

# ----------------- Activity Logging Operations -----------------

def log_activity(teacher_email, action, class_name=None, details=None):
    """
    Logs an action performed by a teacher.
    action: string (e.g. 'Added Student', 'Saved Sheet URL', 'Created Subject')
    class_name: string (optional context)
    details: string (optional detailed info)
    """
    try:
        db = firestore.client()
        db.collection('activity_logs').add({
            "teacher_email": teacher_email,
            "action": action,
            "class_name": class_name or "",
            "details": details or "",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception:
        # Fail silently for logging
        return False

def get_recent_logs(teacher_email=None, hours=24):
    """
    Fetches activity logs from the past N hours.
    If teacher_email is provided, filters by that teacher.
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        db = firestore.client()
        
        # Calculate time threshold
        time_threshold = datetime.now(pytz.utc) - timedelta(hours=hours)
        
        query = db.collection('activity_logs').where(
            filter=firestore.FieldFilter('timestamp', '>=', time_threshold)
        )
        
        if teacher_email:
            query = query.where(
                filter=firestore.FieldFilter('teacher_email', '==', teacher_email)
            )
            
        # Sort by timestamp descending
        docs = query.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        
        logs = []
        for doc in docs:
            data = doc.to_dict()
            # Convert timestamp to string if it exists
            if 'timestamp' in data and data['timestamp']:
                data['timestamp_str'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                data['timestamp_str'] = 'Unknown'
            logs.append(data)
            
        return True, logs
    except Exception as e:
        return False, str(e)

# ----------------- Organization Settings Operations -----------------

def get_org_name():
    try:
        db = firestore.client()
        doc = db.collection('settings').document('organization').get()
        if doc.exists:
            return doc.to_dict().get('org_name', 'Rotary School')
        return 'Rotary School'
    except Exception:
        return 'Rotary School'

def update_org_name(org_name):
    try:
        db = firestore.client()
        db.collection('settings').document('organization').set({
            "org_name": org_name,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
        return True, "Organization name updated"
    except Exception as e:
        return False, str(e)

def get_admin_credentials():
    try:
        db = firestore.client()
        doc = db.collection('settings').document('admin').get()
        if doc.exists:
            data = doc.to_dict()
            return True, data.get('email', 'admin@rems.in'), data.get('password', 'Rotary@123')
        return True, "admin@rems.in", "Rotary@123"
    except Exception:
        return False, "admin@rems.in", "Rotary@123"

def update_admin_credentials(email, password):
    try:
        db = firestore.client()
        db.collection('settings').document('admin').set({
            "email": email,
            "password": password,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
        return True, "Admin credentials updated"
    except Exception as e:
        return False, str(e)

def get_org_logo():
    try:
        db = firestore.client()
        doc = db.collection('settings').document('organization').get()
        if doc.exists:
            return True, doc.to_dict().get('logo_base64', '')
        return True, ''
    except Exception as e:
        return False, str(e)

def update_org_logo(base64_string):
    try:
        db = firestore.client()
        ref = db.collection('settings').document('organization')
        ref.set({
            "logo_base64": base64_string,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
        return True, "Logo updated successfully"
    except Exception as e:
        return False, str(e)

def get_org_settings():
    try:
        db = firestore.client()
        doc = db.collection('settings').document('organization').get()
        if doc.exists:
            return True, doc.to_dict()
        return True, {}
    except Exception as e:
        return False, str(e)

def update_org_settings(settings_dict):
    try:
        db = firestore.client()
        ref = db.collection('settings').document('organization')
        settings_dict["updated_at"] = firestore.SERVER_TIMESTAMP
        ref.set(settings_dict, merge=True)
        return True, "Settings updated successfully"
    except Exception as e:
        return False, str(e)

