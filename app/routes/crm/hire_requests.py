from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app import db
from app.models import HireRequest, HireRequestFile, ActiveProject

crm_hire_requests = Blueprint('crm_hire_requests', __name__, url_prefix='/admin/crm/hire-requests')

VALID_STATUSES = ('pending', 'reviewing', 'accepted', 'in_progress', 'completed', 'declined')


@crm_hire_requests.route('/')
@login_required
def list_hire_requests():
    status_filter = request.args.get('status', '').strip()
    query = HireRequest.query.order_by(HireRequest.created_at.desc())
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter_by(status=status_filter)
    hire_requests = query.all()
    return render_template(
        'admin/hire_requests_list.html',
        hire_requests=hire_requests,
        status_filter=status_filter,
        valid_statuses=VALID_STATUSES,
    )


@crm_hire_requests.route('/<int:id>')
@login_required
def hire_request_detail(id):
    hire_request = HireRequest.query.get_or_404(id)
    files = HireRequestFile.query.filter_by(hire_request_id=id).all()
    return render_template(
        'admin/hire_request_detail.html',
        hire_request=hire_request,
        files=files,
    )


@crm_hire_requests.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    hire_request = HireRequest.query.get_or_404(id)
    new_status = request.form.get('status', '').strip()
    if new_status not in VALID_STATUSES:
        flash(f'Invalid status: {new_status}', 'danger')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    hire_request.status = new_status
    db.session.commit()
    flash(f'Status updated to "{new_status}".', 'success')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/notes', methods=['POST'])
@login_required
def update_notes(id):
    hire_request = HireRequest.query.get_or_404(id)
    hire_request.admin_notes = request.form.get('admin_notes', '').strip()
    db.session.commit()
    flash('Admin notes updated.', 'success')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/accept', methods=['POST'])
@login_required
def accept_request(id):
    hire_request = HireRequest.query.get_or_404(id)

    if hire_request.status == 'accepted':
        flash('This request has already been accepted.', 'warning')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))

    active_project = ActiveProject(
        project_name=hire_request.project_title,
        client_name=hire_request.client_name,
        hire_request_id=hire_request.id,
        status='active',
        source='hire_request',
        is_private=False,
        is_anonymous=False,
    )
    hire_request.status = 'accepted'
    db.session.add(active_project)
    db.session.commit()

    flash(
        f'Hire request accepted. Active project "{active_project.project_name}" created.',
        'success',
    )
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_hire_request(id):
    hire_request = HireRequest.query.get_or_404(id)
    HireRequestFile.query.filter_by(hire_request_id=id).delete()
    db.session.delete(hire_request)
    db.session.commit()
    flash('Hire request deleted.', 'success')
    return redirect(url_for('crm_hire_requests.list_hire_requests'))
