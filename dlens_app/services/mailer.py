import os
import ssl
import smtplib
from email.message import EmailMessage

TLS = os.getenv("SMTP_TLS", "true").lower() == "true"

def send_email(to_addr: str, subject: str, body: str):
    """Send a plaintext email via SMTP with optional TLS and authentication."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("FROM_EMAIL", "no-reply@dlens.local")
    msg["To"] = to_addr
    msg.set_content(body)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")

    if not host:
        raise ValueError("Missing SMTP_HOST environment variable")

    if TLS:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port) as s:
            s.starttls(context=ctx)
            if user and pwd:
                s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            if user and pwd:
                s.login(user, pwd)
            s.send_message(msg)
