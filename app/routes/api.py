from flask import Blueprint, request, jsonify
from app import db
from app.models import ContactSubmission
from app.utils.ses import send_contact_email

api = Blueprint('api', __name__)


@api.route('/contact', methods=['POST'])
def contact_submit():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    project_type = data.get('project_type', '').strip()
    budget_range = data.get('budget_range', '').strip()

    if not name or not email or not message:
        return jsonify({'error': 'Name, email, and message are required.'}), 400

    submission = ContactSubmission(
        name=name,
        email=email,
        subject=subject,
        message=message,
        project_type=project_type,
        budget_range=budget_range,
        ip_address=request.remote_addr,
    )
    db.session.add(submission)
    db.session.commit()

    send_contact_email(name, email, subject, message, project_type, budget_range)

    return jsonify({'success': True, 'message': "Sent! I'll get back to you within 4 hours."})


@api.route('/feeds/refresh', methods=['POST'])
def refresh_feeds():
    feed = request.args.get('feed', 'all')
    try:
        if feed in ('github', 'all'):
            from app.utils.github import clear_cache as clear_github
            clear_github()
        if feed in ('quant', 'all'):
            from app.utils.substack import clear_cache as clear_sub
            clear_sub()
        if feed in ('jarida', 'all'):
            from app.utils.substack import clear_cache as clear_sub
            clear_sub()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
