"""Send email notifications via SMTP (Outlook/Gmail) or print in dev."""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _send_email(subject, body):
    """Send an email notification. Falls back to print in dev."""
    to_email = os.environ.get('CONTACT_TO_EMAIL', 'lagobrian@outlook.com')
    smtp_email = os.environ.get('SMTP_EMAIL', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp-mail.outlook.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if not smtp_email or not smtp_password:
        # Dev mode — just print
        print(f"\n{'='*50}")
        print(f"EMAIL NOTIFICATION")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"{'='*50}")
        print(body)
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email notification failed: {e}")
        return False


def notify_hire_request(hr):
    """Notify when a new hire request is submitted."""
    subject = f"[New Project Application] {hr.project_title}"
    body = f"""New project application received!

Client: {hr.client_name}
Email: {hr.client_email}
Phone: {hr.client_phone or 'Not provided'}
Anonymous: {'Yes' if hr.is_anonymous else 'No'}

Project: {hr.project_title}
Description: {hr.project_description[:500]}

Payment Method: {hr.payment_method or 'Not specified'}
Pricing: {hr.pricing_type or 'Not specified'}
Schedule: {hr.payment_schedule or 'Not specified'}
Deadline: {hr.deadline or 'Not specified'}

Deliverables: {hr.deliverables or 'Not specified'}

AI Summary: {hr.ai_summary or 'None'}

---
Review this application in your CRM dashboard.
"""
    _send_email(subject, body)


def notify_contact(name, email, subject_line, message, project_type=None, budget=None):
    """Notify when a contact form is submitted."""
    subject = f"[Portfolio Contact] {subject_line or 'New inquiry'} from {name}"
    body = f"""New contact form submission!

Name: {name}
Email: {email}
Subject: {subject_line or 'N/A'}
Project Type: {project_type or 'N/A'}
Budget: {budget or 'N/A'}

Message:
{message}

---
Reply directly to {email}
"""
    _send_email(subject, body)
