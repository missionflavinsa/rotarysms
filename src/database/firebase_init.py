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

def create_user(email, password, name="", profile_photo=""):
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
                "profile_photo": ""
            }
            
            # Enrich with Firestore metadata if available
            doc = db.collection('users').document(user.uid).get()
            if doc.exists:
                meta = doc.to_dict()
                user_data["name"] = meta.get("name", "")
                user_data["profile_photo"] = meta.get("profile_photo", "")
                
            users.append(user_data)
        return True, users
    except Exception as e:
        return False, str(e)

def update_user(uid, new_email=None, new_password=None, name=None, profile_photo=None):
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

def add_student(class_id, roll_number, name, apaar_id="", reg_number="", dob="", profile_photo="", email=""):
    try:
        db = firestore.client()
        # Check if student with same roll_number exists in this class
        existing = db.collection('students').where(filter=firestore.FieldFilter('class_id', '==', class_id)).where(filter=firestore.FieldFilter('roll_number', '==', roll_number)).limit(1).stream()
        if len(list(existing)) > 0:
            return False, f"Student with roll number {roll_number} already exists in this class."
            
        _, new_ref = db.collection('students').add({
            "class_id": class_id,
            "roll_number": roll_number,
            "name": name,
            "apaar_id": apaar_id,
            "reg_number": reg_number,
            "dob": str(dob) if dob else "",
            "profile_photo": profile_photo,
            "email": email,
            "created_at": firestore.SERVER_TIMESTAMP
        })
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

def update_student(student_id, roll_number=None, name=None, apaar_id=None, reg_number=None, dob=None, profile_photo=None, email=None):
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
    Expects a pandas DataFrame with columns 'Roll Number', 'Name of the Learner', 'APAAR ID/PEN', 'Registration/Admission Number', 'Date of Birth'.
    """
    try:
        db = firestore.client()
        batch = db.batch()
        
        # Check for requested bulk format or fallback to older format
        has_new_name = 'Name of the Learner' in df.columns
        name_col = 'Name of the Learner' if has_new_name else 'Name'
        roll_col = 'Roll Number'
        
        required_cols = [roll_col, name_col]
        if not all(col in df.columns for col in required_cols):
             return False, f"Excel file must contain at least '{roll_col}' and '{name_col}' columns."
             
        # Optional fields mapping
        has_apaar = 'APAAR ID/PEN' in df.columns
        has_reg = 'Registration/Admission Number' in df.columns
        has_dob = 'Date of Birth' in df.columns
        has_email = 'Email' in df.columns
        
        counter = 0
        for index, row in df.iterrows():
            roll_number = str(row[roll_col]).strip()
            name = str(row[name_col]).strip()
            apaar_id = str(row['APAAR ID/PEN']).strip() if has_apaar and not pd.isna(row['APAAR ID/PEN']) else ""
            reg_num = str(row['Registration/Admission Number']).strip() if has_reg and not pd.isna(row['Registration/Admission Number']) else ""
            dob = str(row['Date of Birth']).strip() if has_dob and not pd.isna(row['Date of Birth']) else ""
            email = str(row['Email']).strip() if has_email and not pd.isna(row['Email']) else ""
            
            # Simple check
            if not roll_number or roll_number == 'nan' or not name or name == 'nan':
                continue
                
            new_ref = db.collection('students').document()
            batch.set(new_ref, {
                "class_id": class_id,
                "roll_number": roll_number,
                "name": name,
                "apaar_id": apaar_id,
                "reg_number": reg_num,
                "dob": dob,
                "profile_photo": "", # Ignore photo on bulk import for now
                "email": email,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            counter += 1
            
            # Firestore batch limit is 500
            if counter % 400 == 0:
                batch.commit()
                batch = db.batch()
                
        # Commit remaining
        if counter % 400 != 0:
            batch.commit()
            
        return True, f"Successfully imported {counter} students."
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
            "sheet_url": "", # Default empty
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

def update_subject(subject_id, name=None, sheet_url=None):
    try:
        db = firestore.client()
        ref = db.collection('subjects').document(subject_id)
        data = {}
        if name is not None: data['name'] = name
        if sheet_url is not None: data['sheet_url'] = sheet_url
        
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

