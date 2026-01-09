import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "student_data.xlsx"
UPLOAD_DIR = "student_documents"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- UNIVERSITY DATA (Expanded) ---
UK_UNIS = ["Oxford", "Cambridge", "UCL", "Imperial", "LSE", "Edinburgh", "Manchester", "King's College", "Warwick", "Bristol", "Glasgow", "Durham", "Southampton", "Birmingham", "Leeds", "Sheffield", "Nottingham", "Queen Mary"]
US_UNIS = ["Harvard", "Stanford", "MIT", "Yale", "Princeton", "Columbia", "UC Berkeley", "UCLA", "UPenn", "NYU", "Cornell", "Dartmouth", "Brown", "Duke", "Johns Hopkins", "Northwestern", "UChicago", "Caltech"]
ALL_UNIS = sorted([f"{u} (UK)" for u in UK_UNIS] + [f"{u} (US)" for u in US_UNIS])

# --- DATABASE FUNCTIONS ---
def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_excel(DB_FILE)
        except: return pd.DataFrame(columns=["Student Name", "Email", "University", "Status", "App Deadline", "Decision Deadline", "Notes"])
    return pd.DataFrame(columns=["Student Name", "Email", "University", "Status", "App Deadline", "Decision Deadline", "Notes"])

def save_document(student_name, uploaded_file):
    student_path = os.path.join(UPLOAD_DIR, student_name.replace(" ", "_"))
    if not os.path.exists(student_path): os.makedirs(student_path)
    file_path = os.path.join(student_path, uploaded_file.name)
    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())

# --- BRANDING & UI ---
st.set_page_config(page_title="Videshway Dashboard", page_icon="🌍", layout="wide")

# Custom CSS for Videshway Branding
st.markdown("""
    <style>
    .main-header { font-size: 36px; font-weight: bold; color: #1E3A8A; }
    .sidebar-brand { font-size: 24px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_index=True)

# Sidebar Branding
st.sidebar.markdown('<p class="sidebar-brand">🌍 Videshway Admin</p>', unsafe_allow_html=True)
menu = ["📈 Global Pipeline", "➕ Add Student", "📂 Document Vault"]
choice = st.sidebar.selectbox("Navigation", menu)

df = load_data()

# --- MAIN LOGIC ---
st.markdown(f'<p class="main-header">Videshway - Client Management Dashboard</p>', unsafe_allow_html=True)

if choice == "➕ Add Student":
    st.subheader("Register New Client")
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Student Full Name")
            email = st.text_input("Email Address")
            university = st.selectbox("Target University", options=ALL_UNIS)
        with col2:
            status = st.selectbox("Current Status", ["Inquiry", "Documents Collected", "Applied", "Offer Received", "Visa Process", "Enrolled"])
            app_deadline = st.date_input("Application Deadline")
            dec_deadline = st.date_input("Expected Decision Date")
        
        notes = st.text_area("Counselor Notes")
        submit = st.form_submit_button("✅ Save to Videshway Database")

        if submit:
            if name:
                new_entry = {
                    "Student Name": name, "Email": email, "University": university,
                    "Status": status, "App Deadline": app_deadline,
                    "Decision Deadline": dec_deadline, "Notes": notes
                }
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                df.to_excel(DB_FILE, index=False)
                st.success(f"Record for {name} created successfully!")
            else:
                st.error("Student Name is required.")

elif choice == "📈 Global Pipeline":
    st.subheader("Current Application Tracking")
    
    if df.empty:
        st.info("No active students in the database.")
    else:
        # KPI Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(df))
        col2.metric("Offers Received", len(df[df['Status'] == "Offer Received"]))
        col3.metric("Applications Sent", len(df[df['Status'] == "Applied"]))

        # Search & Table
        search = st.text_input("🔍 Quick Search (Name or University)")
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as f:
                st.download_button("📥 Export Videshway Data (Excel)", f, file_name="Videshway_Master_List.xlsx")

elif choice == "📂 Document Vault":
    st.subheader("Client Document Repository")
    if df.empty:
        st.warning("Please add students first.")
    else:
        selected_student = st.selectbox("Select Student", df["Student Name"].unique())
        
        st.write(f"### Manage Files for {selected_student}")
        files = st.file_uploader("Upload Passport, Transcripts, SOPs", accept_multiple_files=True)
        if st.button("Upload to Cloud"):
            if files:
                for f in files: save_document(selected_student, f)
                st.success("Documents Uploaded!")
        
        st.write("---")
        st.write("### Download Files")
        student_folder = os.path.join(UPLOAD_DIR, selected_student.replace(" ", "_"))
        if os.path.exists(student_folder):
            for file_name in os.listdir(student_folder):
                with open(os.path.join(student_folder, file_name), "rb") as f:
                    st.download_button(f"📄 {file_name}", f, file_name=file_name)
        else:
            st.info("No documents found for this student.")
