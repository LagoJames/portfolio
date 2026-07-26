"""Send email notifications via Amazon SES SMTP in a background thread."""
import smtplib
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def _smtp_config():
    return {
        'host':     os.environ.get('SES_SMTP_HOST', 'email-smtp.eu-west-1.amazonaws.com'),
        'port':     int(os.environ.get('SES_SMTP_PORT', '587')),
        'user':     os.environ.get('SES_SMTP_USER', ''),
        'password': os.environ.get('SES_SMTP_PASSWORD', ''),
        'from':     os.environ.get('SES_FROM_EMAIL', 'lagobrian@outlook.com'),
    }


def _send_raw(to_email: str, subject: str, body: str, attachment_path: str = None):
    """Send via SES SMTP. Runs in a background thread."""
    cfg = _smtp_config()
    if not cfg['user'] or not cfg['password']:
        print(f'[NOTIFY] SES not configured | would send "{subject}" to {to_email}')
        print(body[:300])
        return
    try:
        msg = MIMEMultipart()
        msg['From']    = cfg['from']
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

        with smtplib.SMTP(cfg['host'], cfg['port'], timeout=10) as server:
            server.starttls()
            server.login(cfg['user'], cfg['password'])
            server.send_message(msg)
        print(f'[NOTIFY] Sent: "{subject}" → {to_email}')
    except Exception as e:
        print(f'[NOTIFY] Failed: {e}')


def _bg(to_email, subject, body, attachment_path=None):
    """Fire-and-forget email in a background thread."""
    threading.Thread(
        target=_send_raw,
        args=(to_email, subject, body, attachment_path),
        daemon=True,
    ).start()


# ── Public helpers ─────────────────────────────────────────────────────────────

def notify_hire_request(hr):
    """Notify you when a new hire request is submitted."""
    to = os.environ.get('CONTACT_TO_EMAIL', 'lagobrian@outlook.com')
    subject = f'[New Proposal] {hr.project_title}'
    body = f"""New project proposal received!

Client:  {hr.client_name or 'Anonymous'}
Email:   {hr.client_email}
Phone:   {hr.client_phone or 'Not provided'}
WhatsApp:{getattr(hr, 'whatsapp_number', None) or 'Not provided'}

Project: {hr.project_title}
{hr.project_description[:500]}

Payment: {hr.payment_method or 'Not specified'} | {hr.pricing_type or 'Not specified'} | {hr.payment_schedule or 'Not specified'}
Amount:  ${hr.total_amount or 0:,.2f} (deposit ${hr.deposit_amount or 0:,.2f})
Deadline:{hr.deadline or 'Not specified'} {getattr(hr, 'deadline_time', '') or ''}
Deadline policy: {getattr(hr, 'deadline_flexibility', 'soft')}
Scope budget: {getattr(hr, 'scope_change_budget', 'fixed')}
Tip: ${getattr(hr, 'tip_amount', 0) or 0:,.2f}
Coffee: {'Yes' if getattr(hr, 'buy_me_a_coffee', False) else 'No'}
Contract signed: {'Yes' if getattr(hr, 'contract_signed', False) else 'No'}
NDA signed: {'Yes' if getattr(hr, 'nda_signed', False) else 'No'}

Deliverables:
{hr.deliverables or 'Not specified'}

AI Summary:
{hr.ai_summary or 'Not specified'}

---
Review in your admin: https://lagobrian.com/admin/hire-requests/{hr.id}
"""
    _bg(to, subject, body)


def notify_contact(name, email, subject_line, message, project_type=None, budget=None):
    """Notify you when a contact form is submitted."""
    to = os.environ.get('CONTACT_TO_EMAIL', 'lagobrian@outlook.com')
    subject = f'[Contact] {subject_line or "New inquiry"} | {name}'
    body = f"""New contact form submission!

Name:         {name}
Email:        {email}
Subject:      {subject_line or 'Not specified'}
Project Type: {project_type or 'Not specified'}
Budget:       {budget or 'Not specified'}

Message:
{message}

---
Reply directly to {email}
"""
    _bg(to, subject, body)


def send_invoice_email(hr, invoice, pdf_path):
    """Email an invoice or receipt PDF to the client."""
    billing_email = hr.invoice_email if hr.invoice_email else hr.client_email
    doc_type = invoice.invoice_type.title()
    subject = f'Your {doc_type} | {hr.project_title}'
    body = f"""Dear {hr.client_name or 'Client'},

Please find attached your {doc_type.lower()} for the following project:

Project:          {hr.project_title}
{doc_type} Number: {invoice.invoice_number}

{"This receipt confirms your payment has been received and recorded." if invoice.invoice_type == "receipt" else "Please review the attached invoice. Payment details and terms are included."}

If you have any questions, reply to this email or message me on WhatsApp.

Best regards,
Lago Brian
lagobrian.com
"""
    _bg(billing_email, subject, body, attachment_path=pdf_path)
