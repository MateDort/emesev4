"""
Example Email Agent Implementation
This is a template for adding email functionality to TARS V2

To use:
1. Rename this file to email_agent.py
2. Add credentials to .env file
3. Follow integration steps in SYSTEM_ANALYSIS.md
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class EmailAgent:
    """
    Handles email sending and reading operations.
    
    Required .env variables:
    - SMTP_SERVER (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - EMAIL_ADDRESS (your email)
    - EMAIL_PASSWORD (app password for Gmail)
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        if not self.email_address or not self.email_password:
            print("[EMAIL] Warning: Email credentials not set in .env file")
    
    async def send_email(self, to: str, subject: str, body: str, 
                        is_html: bool = False) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether body is HTML (default: False)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.email_address or not self.email_password:
            print("[EMAIL] Error: Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Use asyncio.to_thread for blocking SMTP operations
            await asyncio.to_thread(self._send_sync, msg, to)
            print(f"[EMAIL] Successfully sent email to {to}")
            return True
        except Exception as e:
            print(f"[EMAIL] Error sending email: {e}")
            return False
    
    def _send_sync(self, msg: MIMEMultipart, to: str):
        """Synchronous SMTP send (runs in thread)."""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
    
    async def read_emails(self, limit: int = 10) -> List[Dict]:
        """
        Read recent emails from inbox.
        
        Args:
            limit: Maximum number of emails to retrieve
        
        Returns:
            List of email dicts with keys: from, subject, body, date
        """
        # This requires IMAP - example implementation below
        # You'll need to install: pip install imaplib (built-in) or use a library
        
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
            imap_port = int(os.getenv("IMAP_PORT", "993"))
            
            if not self.email_address or not self.email_password:
                print("[EMAIL] Error: Email credentials not configured")
                return []
            
            # Use asyncio.to_thread for blocking IMAP
            emails = await asyncio.to_thread(
                self._read_emails_sync, imap_server, imap_port, limit
            )
            return emails
        except Exception as e:
            print(f"[EMAIL] Error reading emails: {e}")
            return []
    
    def _read_emails_sync(self, imap_server: str, imap_port: int, limit: int) -> List[Dict]:
        """Synchronous IMAP read (runs in thread)."""
        import imaplib
        import email
        from email.header import decode_header
        
        emails = []
        
        try:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select("inbox")
            
            # Search for recent emails
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            
            # Get most recent emails
            for email_id in email_ids[-limit:]:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode subject
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        # Get sender
                        from_addr = msg.get("From")
                        
                        # Get body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        emails.append({
                            "from": from_addr,
                            "subject": subject,
                            "body": body[:500],  # Limit body length
                            "date": msg.get("Date")
                        })
            
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"[EMAIL] IMAP error: {e}")
        
        return emails


# Standalone test
if __name__ == "__main__":
    async def test():
        agent = EmailAgent()
        
        # Test send (uncomment to test)
        # success = await agent.send_email(
        #     to="test@example.com",
        #     subject="Test Email",
        #     body="This is a test email from TARS"
        # )
        # print(f"Send result: {success}")
        
        # Test read (uncomment to test)
        # emails = await agent.read_emails(limit=5)
        # print(f"Found {len(emails)} emails")
        # for e in emails:
        #     print(f"  - {e['subject']} from {e['from']}")
    
    asyncio.run(test())


