import os


def send_contact_email(name, email, subject, message, project_type=None, budget=None):
    """Send contact form submission via Amazon SES (or print in dev)."""
    to_email = os.environ.get('CONTACT_TO_EMAIL', 'lago@lagobrian.com')
    from_email = os.environ.get('SES_FROM_EMAIL', 'hello@lagobrian.com')

    body = f"""
New Contact Form Submission
============================
Name: {name}
Email: {email}
Subject: {subject or 'N/A'}
Project Type: {project_type or 'N/A'}
Budget: {budget or 'N/A'}

Message:
{message}
"""

    if os.environ.get('FLASK_ENV') == 'development':
        print(f"[DEV EMAIL] To: {to_email}")
        print(body)
        return True

    try:
        import boto3
        client = boto3.client('ses', region_name=os.environ.get('AWS_SES_REGION', 'eu-west-1'))
        client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': f'[Portfolio Contact] {subject or "New inquiry"} from {name}'},
                'Body': {'Text': {'Data': body}}
            }
        )
        return True
    except Exception as e:
        print(f"SES Error: {e}")
        return False
