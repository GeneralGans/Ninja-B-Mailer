import smtplib
from email.message import EmailMessage
import pandas as pd
import streamlit as st
import time

# Page Configuration
st.set_page_config(
    page_title="Futuristic Bulk Email Sender",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Futuristic Bulk Email Sender")
st.markdown("Send personalized bulk emails with attachments securely using your SMTP provider (App Passwords recommended).")

# --- Sidebar Configuration: SMTP Settings ---
st.sidebar.header("1️⃣ SMTP Configuration")
smtp_host = st.sidebar.text_input("SMTP Host", value="smtp.gmail.com", help="e.g., smtp.gmail.com")
smtp_port = st.sidebar.number_input("SMTP Port", value=587, help="587 for TLS, 465 for SSL")
smtp_user = st.sidebar.text_input("SMTP Username / Email", help="Your sender email address")
smtp_pass = st.sidebar.text_input("SMTP Password", type="password", help="Use an App Password, not your main password")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Security & Tips")
st.sidebar.info(
    "• Never use your main account password; generate an **App Password** from your mail provider.\n"
    "• Credentials are used solely for the active session and are never stored."
)

# --- Main Layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2️⃣ Upload Recipient List")
    uploaded_file = st.file_uploader("Upload Excel (.xlsx) or CSV (.csv) file", type=["csv", "xlsx"])
    
    df = None
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"Successfully loaded {len(df)} rows!")
            st.dataframe(df.head(3), use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")

with col2:
    st.subheader("4️⃣ Attachments (Optional)")
    uploaded_attachments = st.file_uploader(
        "Upload files to attach to every email", 
        type=["pdf", "png", "jpg", "jpeg", "docx", "txt", "xlsx"], 
        accept_multiple_files=True
    )

st.subheader("3️⃣ Compose Email Content")
sender_name = st.text_input("Sender Name (Optional)", placeholder="e.g., Economic Ninja")
email_subject = st.text_input("Email Subject", placeholder="Hello {Name}, check out our latest update!")
email_body = st.text_area(
    "Email Body (HTML or Plain Text)",
    height=200,
    placeholder="Dear {Name},\n\nYour custom message goes here..."
)

if df is not None:
    st.markdown("💡 **Available Placeholders from your file:** " + ", ".join([f"`{{{col}}}`" for col in df.columns]))

st.subheader("5️⃣ Sending Controls")
delay = st.slider("⏱️ Delay between emails (seconds)", min_value=0, max_value=10, value=2, help="Helps prevent triggering spam filters")

# --- Execution Block ---
if st.button("🚀 Send Bulk Emails", type="primary"):
    # Validation checks
    if not smtp_user or not smtp_pass:
        st.error("Please provide your SMTP Username and Password in the sidebar.")
    elif df is None:
        st.error("Please upload a valid recipient CSV or Excel file.")
    elif 'email' not in [col.lower() for col in df.columns]:
        st.error("Your uploaded file must contain a column named **'email'** (case-insensitive).")
    elif not email_subject or not email_body:
        st.error("Please provide both an email subject and body.")
    else:
        # Find the exact email column name
        email_col = next(col for col in df.columns if col.lower() == 'email')
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        success_count = 0
        fail_count = 0
        total_rows = len(df)

        try:
            # Establish secure SMTP connection
            status_text.text("Connecting to SMTP server...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            
            for index, row in df.iterrows():
                recipient_email = str(row[email_col]).strip()
                
                # Personalize subject and body using row values
                personalized_subject = email_subject
                personalized_body = email_body
                
                for col in df.columns:
                    placeholder = f"{{{col}}}"
                    val = str(row[col])
                    personalized_subject = personalized_subject.replace(placeholder, val)
                    personalized_body = personalized_body.replace(placeholder, val)
                
                # Construct message
                msg = EmailMessage()
                msg['Subject'] = personalized_subject
                msg['From'] = f"{sender_name} <{smtp_user}>" if sender_name else smtp_user
                msg['To'] = recipient_email
                msg.set_content(personalized_body)
                
                # Attach files if any uploaded
                if uploaded_attachments:
                    for file in uploaded_attachments:
                        file.seek(0) # Reset pointer
                        file_data = file.read()
                        file_name = file.name
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                
                try:
                    server.send_message(msg)
                    success_count += 1
                    with log_container:
                        st.success(f"[{index+1}/{total_rows}] Sent successfully to: {recipient_email}")
                except Exception as mail_err:
                    fail_count += 1
                    with log_container:
                        st.error(f"[{index+1}/{total_rows}] Failed to send to {recipient_email}: {mail_err}")
                
                # Update progress
                progress_bar.progress((index + 1) / total_rows)
                time.sleep(delay)
                
            server.quit()
            status_text.success(f"✨ Finished! Successfully sent: {success_count} | Failed: {fail_count}")
            
        except Exception as conn_err:
            st.error(f"Failed to connect to SMTP server. Check your credentials and host settings. Error: {conn_err}")