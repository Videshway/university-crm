import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "student_data.xlsx"
UPLOAD_DIR = "student_documents"

# --- USER ACCESS DATA ---
# In a real app, these would be in a database or st.secrets
# Format: { "username": {"password": "password123", "name": "Full Name", "role": "admin/agent"} }
USER_DB = {
    "admin": {"password": "adminvideshway", "name": "Main Admin", "role": "admin"},
    "agent1": {"password": "agent1videshway", "name": "Agent Rahul", "role": "agent"},
    "agent2": {"password": "agent2videshway", "name": "Agent Priya", "role": "agent"}
}

# --- INITIALIZATION ---
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

# --- FUNCTIONS ---
def load_data():
    cols = ["Student Name", "Email", "University", "Status", "App Deadline", "Decision Deadline", "Notes", "Assigned Agent"]
    if os.path.exists(DB_FILE):
        try:
            return pd.read_excel(DB_FILE)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_document(agent_name, student_name, uploaded_file):
    # Documents stored as: student_documents/AgentName/StudentName/file.pdf
    agent_folder = agent_name.replace(" ", "_")
    student_folder = student_name.replace(" ", "_")
    path = os.path.join(UPLOAD_DIR, agent_folder, student_folder)
    
    if not os.path.exists(path):
        os.makedirs(path)
        
    file_path = os.path.join(path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- LOGIN SCREEN ---
def login_page():
    st.set_page_config(page_title="Videshway Login", page_icon="🌍")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://via.placeholder.com/150?text=Videshway", width=150) # Replace with your logo URL
        st.title("Videshway Login")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if user in USER_DB and USER_DB[user]["password"] == pwd:
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.session_state['user_name'] = USER_DB[user]["name"]
                st.session_state['role'] = USER_DB[user]["role"]
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- MAIN DASHBOARD ---
def main_dashboard():
    st.set_page_config(page_title="Videshway Dashboard", page_icon="🌍", layout="wide")
    
    user_info = USER_DB[st.session_state['user']]
    agent_name = user_info['name']
    role = user_info['role']

    # Sidebar
    st.sidebar.markdown(f"### Welcome, {agent_name}")
    st.sidebar.info(f"Role: {role.capitalize()}")
    
    menu = ["📈 Global Pipeline", "➕ Add Student", "📂 Document Vault"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    df = load_data()

    # --- BRANDING ---
    st.markdown(f'<h1 style="color: #1E3A8A;">Videshway Dashboard</h1>', unsafe_allow_html=True)

    if choice == "➕ Add Student":
        st.subheader("Register New Client")
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Student Name")
                email = st.text_input("Email")
                uni = st.selectbox("University", ["Oxford (UK)", "Harvard (US)", "Cambridge (UK)", "Stanford (US)"]) # Expand this list
            with col2:
                status = st.selectbox("Status", ["Applied", "Offer Received", "Visa", "Enrolled"])
                deadline = st.date_input("Deadline")
            
            notes = st.text_area("Notes")
            submit = st.form_submit_button("Save Application")

            if submit and name:
                new_data = {
                    "Student Name": name, "Email": email, "University": uni,
                    "Status": status, "App Deadline": deadline, "Notes": notes,
                    "Assigned Agent": agent_name # Records who created it
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                df.to_excel(DB_FILE, index=False)
                st.success(f"Added {name} to your pipeline.")

    elif choice == "📈 Global Pipeline":
        st.subheader("Application Tracking")
        
        # FILTERING LOGIC
        if role == "admin":
            display_df = df # Admins see all
            st.write("📊 *Showing all records (Admin View)*")
        else:
            display_df = df[df["Assigned Agent"] == agent_name] # Agents see only theirs
            st.write(f"📊 *Showing records for {agent_name}*")

        if display_df.empty:
            st.info("No records found.")
        else:
            search = st.text_input("Search...")
            filtered = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.dataframe(filtered, use_container_width=True)

    elif choice == "📂 Document Vault":
        st.subheader("Document Vault")
        
        # Filter student list by agent ownership
        if role == "admin":
            available_students = df["Student Name"].unique()
        else:
            available_students = df[df["Assigned Agent"] == agent_name]["Student Name"].unique()

        if len(available_students) == 0:
            st.warning("No students found in your pipeline.")
        else:
            selected_student = st.selectbox("Select Student", available_students)
            
            # Record who is uploading
            owner_agent = df[df["Student Name"] == selected_student]["Assigned Agent"].values[0]

            files = st.file_uploader("Upload Docs", accept_multiple_files=True)
            if st.button("Upload"):
                for f in files:
                    save_document(owner_agent, selected_student, f)
                st.success("Documents Saved.")

            st.write("---")
            st.write("### Download Files")
            # Look in the specific agent's folder
            path = os.path.join(UPLOAD_DIR, owner_agent.replace(" ", "_"), selected_student.replace(" ", "_"))
            if os.path.exists(path):
                for f_name in os.listdir(path):
                    with open(os.path.join(path, f_name), "rb") as f:
                        st.download_button(f"📄 {f_name}", f, file_name=f_name, key=f_name)
            else:
                st.info("No files uploaded yet.")

# --- RUN APP ---
if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
