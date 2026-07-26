from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app import db
from app.models import HireRequest, HireRequestFile, ActiveProject
import os, uuid
from datetime import datetime, timezone
from flask import send_file

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
        req=hire_request,
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

    # WhatsApp alert to client
    try:
        from app.utils.whatsapp import alert_proposal_accepted
        from app.utils.helpers import get_setting
        delay = int(get_setting('whatsapp_start_delay_days') or 0)
        alert_proposal_accepted(hire_request, start_in_days=delay)
    except Exception:
        pass

    flash(
        f'Hire request accepted. Active project "{active_project.project_name}" created.',
        'success',
    )
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/confirm-payment', methods=['POST'])
@login_required
def confirm_payment(id):
    from app.models import Invoice
    from app.utils.invoice_pdf import generate_receipt as gen_rec
    hire_request = HireRequest.query.get_or_404(id)
    hire_request.payment_status = 'confirmed'
    db.session.commit()
    # Auto-generate receipt if not already exists
    existing = Invoice.query.filter_by(hire_request_id=id, invoice_type='receipt').first()
    if not existing:
        inv = Invoice.query.filter_by(hire_request_id=id, invoice_type='invoice').first()
        inv_num = inv.invoice_number if inv else f'INV-{datetime.now(timezone.utc).strftime("%Y%m")}-{id:04d}'
        rec_num = f'REC-{datetime.now(timezone.utc).strftime("%Y%m")}-{id:04d}'
        rel_path = os.path.join('invoices', f'{rec_num}.pdf')
        abs_path = os.path.join('uploads', rel_path)
        try:
            gen_rec(hire_request, inv_num, rec_num, abs_path)
            rec = Invoice(hire_request_id=id, invoice_number=rec_num,
                          invoice_type='receipt', pdf_path=rel_path)
            db.session.add(rec)
            db.session.commit()
            if not hire_request.invoice_opt_out:
                from app.utils.notify import send_invoice_email
                send_invoice_email(hire_request, rec, abs_path)
        except Exception as e:
            print(f'[RECEIPT] Auto-gen failed: {e}')
    # WhatsApp alert to client
    try:
        from app.utils.whatsapp import alert_payment_received
        paid = hire_request.deposit_amount or hire_request.total_amount or 0
        remaining = max((hire_request.total_amount or 0) - paid, 0)
        alert_payment_received(hire_request, amount_paid=paid, amount_remaining=remaining)
    except Exception:
        pass

    flash('Payment confirmed. Receipt generated.', 'success')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/generate-invoice', methods=['POST'])
@login_required
def generate_invoice(id):
    from app.utils.invoice_pdf import generate_invoice as gen_inv
    from app.models import Invoice
    hr = HireRequest.query.get_or_404(id)
    # Check if invoice already exists
    existing = Invoice.query.filter_by(hire_request_id=id, invoice_type='invoice').first()
    if existing:
        flash('Invoice already exists. Download it below.', 'warning')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    inv_num = f'INV-{datetime.now(timezone.utc).strftime("%Y%m")}-{id:04d}'
    rel_path = os.path.join('invoices', f'{inv_num}.pdf')
    abs_path = os.path.join('uploads', rel_path)
    gen_inv(hr, inv_num, abs_path)
    inv = Invoice(hire_request_id=id, invoice_number=inv_num,
                  invoice_type='invoice', pdf_path=rel_path)
    db.session.add(inv)
    db.session.commit()
    # Email if not opted out
    if not hr.invoice_opt_out:
        try:
            from app.utils.notify import send_invoice_email
            send_invoice_email(hr, inv, abs_path)
        except Exception as e:
            print(f'[INVOICE] Email failed: {e}')
    flash(f'Invoice {inv_num} generated.', 'success')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/generate-receipt', methods=['POST'])
@login_required
def generate_receipt(id):
    from app.utils.invoice_pdf import generate_receipt as gen_rec
    from app.models import Invoice
    hr = HireRequest.query.get_or_404(id)
    if hr.payment_status not in ('confirmed',):
        flash('Payment must be confirmed before generating a receipt.', 'danger')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    existing = Invoice.query.filter_by(hire_request_id=id, invoice_type='receipt').first()
    if existing:
        flash('Receipt already exists. Download it below.', 'warning')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    inv = Invoice.query.filter_by(hire_request_id=id, invoice_type='invoice').first()
    inv_num = inv.invoice_number if inv else f'INV-{datetime.now(timezone.utc).strftime("%Y%m")}-{id:04d}'
    rec_num = f'REC-{datetime.now(timezone.utc).strftime("%Y%m")}-{id:04d}'
    rel_path = os.path.join('invoices', f'{rec_num}.pdf')
    abs_path = os.path.join('uploads', rel_path)
    gen_rec(hr, inv_num, rec_num, abs_path)
    rec = Invoice(hire_request_id=id, invoice_number=rec_num,
                  invoice_type='receipt', pdf_path=rel_path)
    db.session.add(rec)
    db.session.commit()
    if not hr.invoice_opt_out:
        try:
            from app.utils.notify import send_invoice_email
            send_invoice_email(hr, rec, abs_path)
        except Exception as e:
            print(f'[RECEIPT] Email failed: {e}')
    flash(f'Receipt {rec_num} generated.', 'success')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/invoices/<int:inv_id>/download')
@login_required
def download_invoice(id, inv_id):
    from app.models import Invoice
    inv = Invoice.query.filter_by(id=inv_id, hire_request_id=id).first_or_404()
    abs_path = os.path.join('uploads', inv.pdf_path)
    if not os.path.exists(abs_path):
        flash('PDF file not found.', 'danger')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    return send_file(abs_path, as_attachment=True,
                     download_name=os.path.basename(inv.pdf_path),
                     mimetype='application/pdf')


@crm_hire_requests.route('/<int:id>/alert-milestone', methods=['POST'])
@login_required
def alert_milestone(id):
    hr = HireRequest.query.get_or_404(id)
    milestone = request.form.get('milestone_name', '').strip()
    note = request.form.get('note', '').strip()
    if not milestone:
        flash('Milestone name is required.', 'error')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    try:
        from app.utils.whatsapp import alert_milestone_done
        alert_milestone_done(hr, milestone, note)
        flash(f'Milestone alert sent: "{milestone}"', 'success')
    except Exception as e:
        flash(f'Alert failed: {e}', 'error')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/alert-delivered', methods=['POST'])
@login_required
def alert_delivered(id):
    hr = HireRequest.query.get_or_404(id)
    note = request.form.get('note', '').strip()
    hr.status = 'completed'
    db.session.commit()
    try:
        from app.utils.whatsapp import alert_project_delivered
        alert_project_delivered(hr, note)
        flash('Delivery alert sent. Status set to completed.', 'success')
    except Exception as e:
        flash(f'Alert failed: {e}', 'error')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/alert-revision', methods=['POST'])
@login_required
def alert_revision(id):
    hr = HireRequest.query.get_or_404(id)
    note = request.form.get('note', '').strip()
    try:
        from app.utils.whatsapp import alert_revision_done
        alert_revision_done(hr, note)
        flash('Revision alert sent.', 'success')
    except Exception as e:
        flash(f'Alert failed: {e}', 'error')
    return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))


@crm_hire_requests.route('/<int:id>/alert-need-info', methods=['POST'])
@login_required
def alert_need_info(id):
    hr = HireRequest.query.get_or_404(id)
    what = request.form.get('what_needed', '').strip()
    if not what:
        flash('Please describe what information you need.', 'error')
        return redirect(url_for('crm_hire_requests.hire_request_detail', id=id))
    try:
        from app.utils.whatsapp import alert_need_info as _alert
        _alert(hr, what)
        flash('Info request alert sent.', 'success')
    except Exception as e:
        flash(f'Alert failed: {e}', 'error')
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
