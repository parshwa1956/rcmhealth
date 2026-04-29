
"""
Simple welcome email sender for Tuba RCM app.

This is intentionally configurable for local/testing use.
By default, sending is disabled until SMTP settings are filled in.
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple

SMTP_ENABLED = False
SMTP_HOST = ""
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SMTP_USE_TLS = True
SMTP_FROM_EMAIL = ""
SMTP_FROM_NAME = "Tuba Revenue Integrity Platform Admin"


def send_welcome_email(
    *,
    user_name: str,
    user_email: str,
    temp_password: str,
    login_url: str,
    environment_name: str,
) -> Tuple[bool, str]:
    """Send welcome email with temp password and login URL.

    Returns:
        (success, message)
    """
    if not SMTP_ENABLED:
        return False, "Email sending is disabled. Update SMTP settings in email_sender.py."

    required = [SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL]
    if not all(required):
        return False, "SMTP settings are incomplete in email_sender.py."

    subject = "Your Tuba Revenue Integrity & Denials Prevention Platform Access"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #0f2345; line-height: 1.6;">
        <p>Hello {user_name or user_email},</p>

        <p>Your account has been created for the <b>Tuba Revenue Integrity & Denials Prevention Platform</b>.</p>

        <p><b>Environment:</b> {environment_name}<br>
        <b>Username:</b> {user_email}<br>
        <b>Temporary Password:</b> {temp_password}<br>
        <b>Login Link:</b> <a href="{login_url}">{login_url}</a></p>

        <p>For security, you will be required to change your password the first time you sign in.</p>

        <p>If you have any questions or need assistance accessing the platform, please contact the administrator.</p>

        <p>Thank you,<br>
        Tuba Revenue Integrity Platform Admin</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = user_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [user_email], msg.as_string())
        return True, f"Welcome email sent to {user_email}."
    except Exception as exc:
        return False, f"Email send failed: {exc}"
