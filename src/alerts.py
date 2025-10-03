import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_alert(subject, message, is_error=False):
    """Send email alert"""
    
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        print("⚠️ Email credentials not configured")
        return
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"{'❌ ERROR' if is_error else '✅ SUCCESS'}: {subject}"
        
        # Email body
        body = f"""
Stock ETL Pipeline Alert

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

---
This is an automated message from your ETL pipeline.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        
        print(f"📧 Alert sent to {receiver}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")