from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import ContactSubmission

crm_contacts = Blueprint('crm_contacts', __name__, template_folder='../../../templates')


@crm_contacts.route('/')
@login_required
def list_contacts():
    contacts = (
        db.session.query(ContactSubmission)
        .order_by(ContactSubmission.created_at.desc())
        .all()
    )
    unread_count = sum(1 for c in contacts if not c.is_read)
    return render_template(
        'admin/contacts_list.html',
        contacts=contacts,
        unread_count=unread_count,
    )


@crm_contacts.route('/<int:id>')
@login_required
def contact_detail(id):
    contact = db.session.get(ContactSubmission, id)
    if contact is None:
        flash('Contact submission not found.', 'danger')
        return redirect(url_for('crm_contacts.list_contacts'))

    if not contact.is_read:
        contact.is_read = True
        db.session.commit()

    return render_template('admin/contact_detail.html', contact=contact)


@crm_contacts.route('/<int:id>/mark-read', methods=['POST'])
@login_required
def mark_read(id):
    contact = db.session.get(ContactSubmission, id)
    if contact is None:
        flash('Contact submission not found.', 'danger')
        return redirect(url_for('crm_contacts.list_contacts'))

    contact.is_read = not contact.is_read
    db.session.commit()
    status = 'read' if contact.is_read else 'unread'
    flash(f'Message marked as {status}.', 'success')

    next_page = request.args.get('next') or request.referrer
    return redirect(next_page or url_for('crm_contacts.list_contacts'))


@crm_contacts.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_contact(id):
    contact = db.session.get(ContactSubmission, id)
    if contact is None:
        flash('Contact submission not found.', 'danger')
        return redirect(url_for('crm_contacts.list_contacts'))

    db.session.delete(contact)
    db.session.commit()
    flash('Contact submission deleted.', 'success')
    return redirect(url_for('crm_contacts.list_contacts'))


@crm_contacts.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    db.session.query(ContactSubmission).filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All messages marked as read.', 'success')
    return redirect(url_for('crm_contacts.list_contacts'))
