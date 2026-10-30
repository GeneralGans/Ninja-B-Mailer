import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time

st.set_page_config(page_title="Economic Ninja Bulk Mailer", page_icon="🚀", layout="centered")

st.title("🚀 Economic Ninja Bulk Email Sender")
st.markdown("Send personalized bulk emails with attachments securely using your SMTP provider.")

# Sidebar Configuration
st.sidebar.header("🔐 SMTP Configuration")
smtp_server = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("SMTP Port", value=587, step=1)
smtp_user = st.sidebar.text_input("SMTP Username (Email)", type="default")
smtp_pass = st.sidebar.text_input("SMTP App Password", type="password")

st.sidebar.markdown("---")
st.sidebar.info("Tip: For Gmail, use an **App Password** generated from your Google Account security settings.")

# 1. Upload Recipient List
st.subheader("2️⃣ Upload Recipient List")
uploaded_file = st.file_uploader("Upload Excel (.xlsx) or CSV (.csv) file", type=["csv", "xlsx"])

df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success(f"Successfully loaded {len(df)} recipients!")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error reading file: {e}")

# 2. Attachments
st.subheader("4️⃣ Attachments (Optional)")
uploaded_attachments = st.file_uploader(
    "Upload files to attach to every email",
    type=["pdf", "png", "jpg", "jpeg", "docx", "txt", "xlsx"],
    accept_multiple_files=True
)

# 3. Compose Email Content
st.subheader("3️⃣ Compose Email Content")
sender_name = st.text_input("Sender Name (Optional)", placeholder="e.g., Economic Ninja")
email_subject = st.text_input("Email Subject", placeholder="Hello {Name}, check out our latest update!")

email_body = st.text_area(
    "Email Body (HTML or Plain Text)",
    height=180,
    placeholder="Dear {Name},\n\nYour custom message goes here..."
)

email_signature = st.text_area(
    "Email Signature (HTML Supported)",
    height=150,
    placeholder="Paste your HTML signature block here..."
)

if df is not None:
    placeholders_str = ", ".join([f"{{{col}}}" for col in df.columns])
    st.markdown(f"💡 **Available Placeholders from your file:** {placeholders_str}")

# --- Execution Block ---
st.subheader("5️⃣ Sending Controls")
delay = st.slider("⏱️ Delay between emails (seconds)", min_value=0, max_value=10, value=2, help="Helps prevent triggering spam filters")

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
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            
            for index, row in df.iterrows():
                recipient_email = str(row[email_col]).strip()
                if not recipient_email or recipient_email.lower() == 'nan':
                    fail_count += 1
                    continue
                
                # Format personalized body
                formatted_body = email_body
                for col in df.columns:
                    placeholder = f"{{{col}}}"
                    val = str(row[col]) if pd.notna(row[col]) else ""
                    formatted_body = formatted_body.replace(placeholder, val)
                
                # Combine body and signature block
                full_message = f"{formatted_body}<br><br>{email_signature}"
                
                # Create message
                msg = MIMEMultipart()
                msg['From'] = f"{sender_name} <{smtp_user}>" if sender_name else smtp_user
                msg['To'] = recipient_email
                msg['Subject'] = email_subject
                
                # Attach body as HTML
                msg.attach(MIMEText(full_message, 'html'))
                
                # Attach files if any
                if uploaded_attachments:
                    for att in uploaded_attachments:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(att.getvalue())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{att.name}"')
                        msg.attach(part)
                
                try:
                    server.sendmail(smtp_user, recipient_email, msg.as_string())
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    with log_container:
                        st.error(f"Failed to send to {recipient_email}: {e}")
                
                # Update progress
                progress = (index + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"Processing {index + 1} of {total_rows}...")
                
                if delay > 0:
                    time.sleep(delay)
                    
            server.quit()
            st.success(f"Finished! Successfully sent: {success_count} | Failed: {fail_count}")
            
        except Exception as e:
            st.error(f"SMTP Connection Error: {e}")
