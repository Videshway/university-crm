import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "student_data.xlsx"
UPLOAD_DIR = "student_documents"

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- UNIVERSITY DATA ---
# (Added a few more for you)
UK_UNIS = ["Oxford", "Cambridge", "UCL", "Imperial", "LSE", "Edinburgh", "Manchester", "King's College", "Warwick", "Bristol", "Glasgow", "Durham", "Southampton", "Birmingham"]
US_UNIS = ["Harvard", "Stanford", "MIT", "Yale", "Princeton", "Columbia", "UC Berkeley", "UCLA", "UPenn", "NYU", "Cornell", "Dartmouth", "Brown", "Duke", "Johns Hopkins"]
ALL_UNIS = sorted([f"{u} (UK)" for u in UK_UNIS] + [f"{u} (US)" for u in US_UNIS])

# --- DATABASE FUNCTIONS ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_excel(DB_FILE)
        except:
            return pd.DataFrame(columns=["Student Name", "Email", "University", "Status", "App Deadline", "Decision Deadline", "Notes"])
    else:
        return pd.DataFrame(columns=["Student Name", "Email", "University", "Status", "App Deadline", "Decision Deadline", "Notes"])

def save_document(student_name, uploaded_file):
    student_path = os.path.join(UPLOAD_DIR, student_name.replace(" ", "_"))
    if not os.path.exists(student_path):
        os.makedirs(student_path)
    
    file_path = os.path.join(student_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# --- UI INTERFACE ---
st.set_page_config(page_title="UniApply CRM Pro", layout="wide")
st.title("🎓 University Application CRM + Document Manager")

menu = ["Pipeline View", "Add New Application", "Document Vault"]
choice = st.sidebar.selectbox("Navigation", menu)

df = load_data()

if choice == "Add New Application":
    st.subheader("📝 New Application Entry")
    
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Full Name")
            email = st.text_input("Email Address")
            university = st.selectbox("Select University", options=ALL_UNIS)
            status = st.selectbox("Status", ["Inquiry", "Applied", "Offer Received", "Waitlisted", "Enrolled"])
            
        with col2:
            app_deadline = st.date_input("Application Submission Deadline")
            dec_deadline = st.date_input("Decision Expected By")
            notes = st.text_area("Internal Notes")
        
        submit = st.form_submit_button("Save Application to Excel")

        if submit:
            if name:
                new_entry = {
                    "Student Name": name, "Email": email, "University": university,
                    "Status": status, "App Deadline": app_deadline,
                    "Decision Deadline": dec_deadline, "Notes": notes
                }
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                df.to_excel(DB_FILE, index=False)
                st.success(f"Successfully saved {name}'s application! Refresh the page to see changes.")
            else:
                st.error("Please enter a student name.")

elif choice == "Pipeline View":
    st.subheader("📊 Global Application Pipeline")
    
    if df.empty:
        st.info("No records found. Go to 'Add New Application' to create your first record.")
    else:
        search_query = st.text_input("Search student or university...")
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        st.dataframe(filtered_df, use_container_width=True)
        
        # Only show download button if file exists
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as f:
                st.download_button(
                    label="📥 Download Database as Excel",
                    data=f,
                    file_name="UniCRM_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif choice == "Document Vault":
    st.subheader("📂 Document Management")
    
    if df.empty:
        st.warning("No students found. Add a student first.")
    else:
        student_list = df["Student Name"].unique()
        selected_student = st.selectbox("Select Student", student_list)
        
        st.write(f"### Upload for {selected_student}")
        uploaded_files = st.file_uploader("Upload Passport, Transcripts, etc.", accept_multiple_files=True)
        
        if st.button("Save Documents"):
            if uploaded_files:
                for f in uploaded_files:
                    save_document(selected_student, f)
                st.success(f"Saved {len(uploaded_files)} files.")
            else:
                st.error("Please select files first.")

        st.write("---")
        st.write("### Existing Documents")
        student_folder = os.path.join(UPLOAD_DIR, selected_student.replace(" ", "_"))
        if os.path.exists(student_folder):
            files = os.listdir(student_folder)
            for file_name in files:
                col_a, col_b = st.columns([0.8, 0.2])
                col_a.write(f"📄 {file_name}")
                with open(os.path.join(student_folder, file_name), "rb") as f:
                    col_b.download_button("Download", f, file_name=file_name, key=file_name)
        else:
            st.info("No documents uploaded yet.")