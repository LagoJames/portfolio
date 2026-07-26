import csv
import os
from functools import wraps
from io import BytesIO, StringIO

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import db
from app.models import (PMClient, PMProject, PMTask, PMTaskLog,
                        PMPayment, PMInvoice, PMExpense, PMDailyFocus)
from datetime import date, datetime, timedelta

crm_pm = Blueprint('crm_pm', __name__, url_prefix='/admin/pm')

PROJECT_STATUS_LABELS = {
    'active': 'Ongoing',
    'completed': 'Completed',
    'on_hold': 'On Hold',
    'cancelled': 'Cancelled',
}

TASK_STATUS_LABELS = {
    'not_started': 'Not Started',
    'in_progress': 'Ongoing',
    'completed': 'Completed',
    'blocked': 'Blocked',
}

INVOICE_STATUS_LABELS = {
    'paid': 'Paid',
    'partial': 'Partially Paid',
    'unpaid': 'Unpaid',
}


def _parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d',):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _parse_date_only(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _week_bounds():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _pm_owner_email():
    return (
        current_app.config.get('PM_OWNER_EMAIL')
        or os.getenv('PM_OWNER_EMAIL')
        or current_app.config.get('CONTACT_TO_EMAIL')
        or ''
    ).strip().lower()


def _pm_freelancer_email():
    return (current_app.config.get('PM_FREELANCER_EMAIL') or os.getenv('PM_FREELANCER_EMAIL') or '').strip().lower()


def _pm_role():
    if not current_user.is_authenticated:
        return None
    email = (current_user.email or '').strip().lower()
    freelancer_email = _pm_freelancer_email()
    if freelancer_email and email == freelancer_email:
        return 'freelancer'
    return 'pm'


@crm_pm.app_context_processor
def inject_pm_access():
    role = _pm_role()
    return {
        'pm_role': role,
        'pm_can_write': role == 'pm',
        'pm_can_log': role == 'freelancer',
        'project_status_labels': PROJECT_STATUS_LABELS,
        'task_status_labels': TASK_STATUS_LABELS,
        'invoice_status_labels': INVOICE_STATUS_LABELS,
    }


def _role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            role = _pm_role()
            if role not in allowed_roles:
                flash('You do not have permission to access that PM section.', 'warning')
                return redirect(url_for('crm_pm.overview'))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _normalize_project_status(value):
    mapping = {
        'ongoing': 'active',
        'active': 'active',
        'completed': 'completed',
        'on_hold': 'on_hold',
        'cancelled': 'cancelled',
    }
    return mapping.get((value or 'active').strip().lower(), 'active')


def _normalize_task_status(value):
    mapping = {
        'todo': 'not_started',
        'not_started': 'not_started',
        'ongoing': 'in_progress',
        'in_progress': 'in_progress',
        'review': 'in_progress',
        'done': 'completed',
        'completed': 'completed',
        'blocked': 'blocked',
    }
    return mapping.get((value or 'not_started').strip().lower(), 'not_started')


def _normalize_invoice_status(value):
    mapping = {
        'paid': 'paid',
        'partial': 'partial',
        'partially_paid': 'partial',
        'unpaid': 'unpaid',
    }
    return mapping.get((value or 'unpaid').strip().lower(), 'unpaid')


def _project_receipt_id(project, invoice=None):
    client_code = f'{project.client_id:03d}' if project and project.client_id else '000'
    invoice_code = invoice.invoice_number if invoice else 'GEN'
    return f'{client_code}-{invoice_code}-RCT'


def _serialize_rows(section):
    if section == 'clients':
        rows = []
        for client in PMClient.query.order_by(PMClient.name).all():
            if client.pm_projects:
                for project in client.pm_projects:
                    rows.append({
                        'Client Name': client.name,
                        'Client ID': client.id,
                        'Project Name': project.name,
                        'Status': PROJECT_STATUS_LABELS.get(_normalize_project_status(project.status), project.status or ''),
                        'Budget': project.budget or 0,
                        'Amount Paid': project.paid,
                        'Balance': project.balance,
                        'Notes': project.notes or client.notes or '',
                    })
            else:
                rows.append({
                    'Client Name': client.name,
                    'Client ID': client.id,
                    'Project Name': '',
                    'Status': '',
                    'Budget': '',
                    'Amount Paid': '',
                    'Balance': '',
                    'Notes': client.notes or '',
                })
        return rows

    if section == 'tasks':
        return [{
            'Task ID': task.task_id_code or '',
            'Client': task.project.client.name if task.project and task.project.client else '',
            'Project': task.project.name if task.project else '',
            'Task Description': task.description,
            'Est. Duration (hrs)': task.estimated_hours if task.estimated_hours is not None else '',
            'Status': TASK_STATUS_LABELS.get(_normalize_task_status(task.status), task.status or ''),
            'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'Priority': task.priority or '',
            'PM Notes': task.notes or '',
        } for task in PMTask.query.order_by(PMTask.due_date, PMTask.id).all()]

    if section == 'daily_focus':
        return [{
            'Date': entry.date.isoformat() if entry.date else '',
            'Task ID': entry.task.task_id_code if entry.task else '',
            'Task Description': entry.task.description if entry.task else '',
            'Est. Time (hrs)': entry.est_time or '',
            'Status': TASK_STATUS_LABELS.get(_normalize_task_status(entry.status), entry.status or ''),
            'Notes': entry.notes or '',
        } for entry in PMDailyFocus.query.order_by(PMDailyFocus.date.desc(), PMDailyFocus.id.desc()).all()]

    if section == 'task_log':
        return [{
            'Date': log.date.strftime('%Y-%m-%d') if log.date else '',
            'Task ID': log.task.task_id_code if log.task else '',
            'Actual Time Spent': log.actual_time or '',
            'Status': TASK_STATUS_LABELS.get(_normalize_task_status(log.status), log.status or ''),
            'Notes': log.notes or '',
        } for log in PMTaskLog.query.order_by(PMTaskLog.date.desc(), PMTaskLog.id.desc()).all()]

    if section == 'payments':
        rows = []
        for payment in PMPayment.query.order_by(PMPayment.date.desc(), PMPayment.id.desc()).all():
            project = payment.project
            prior_paid = sum(
                p.amount or 0 for p in project.payments
                if p.id != payment.id and p.date and payment.date and (p.date < payment.date or (p.date == payment.date and p.id < payment.id))
            ) if project else 0
            rows.append({
                'Date': payment.date.strftime('%Y-%m-%d') if payment.date else '',
                'Client Name': project.client.name if project and project.client else '',
                'Client ID': project.client_id if project else '',
                'Project Name': project.name if project else '',
                'Status': PROJECT_STATUS_LABELS.get(_normalize_project_status(project.status if project else ''), ''),
                'Budget': project.budget if project and project.budget is not None else '',
                'Amount Paid So Far': prior_paid,
                'Amount Paid Today': payment.amount or 0,
                'Invoice ID': payment.invoice_id or '',
                'Receipt ID': payment.receipt_id or '',
                'Payment Method': payment.payment_method or '',
                'Balance': project.balance if project else '',
                'Notes': payment.notes or '',
            })
        return rows

    if section == 'invoices':
        return [{
            'Date': invoice.date.strftime('%Y-%m-%d') if invoice.date else '',
            'Client Name': invoice.project.client.name if invoice.project and invoice.project.client else '',
            'Client ID': invoice.project.client_id if invoice.project else '',
            'Project Name': invoice.project.name if invoice.project else '',
            'Invoice Number': invoice.invoice_number or '',
            'Invoiced Task (ID)': invoice.task_id or '',
            'Invoice Amount': invoice.amount or 0,
            'Payment Status': INVOICE_STATUS_LABELS.get(_normalize_invoice_status(invoice.payment_status), invoice.payment_status or ''),
                'Payment Date': '',
            'Notes': invoice.notes or '',
        } for invoice in PMInvoice.query.order_by(PMInvoice.date.desc(), PMInvoice.id.desc()).all()]

    if section == 'expenses':
        return [{
            'Date': expense.date.strftime('%Y-%m-%d') if expense.date else '',
            'Item': expense.item,
            'Cost': expense.cost or 0,
            'Category': expense.category or '',
            'Linked Project': expense.project.name if getattr(expense, 'project', None) else '',
            'Notes': expense.notes or '',
        } for expense in PMExpense.query.order_by(PMExpense.date.desc(), PMExpense.id.desc()).all()]

    return []


def _export_csv(filename, rows):
    output = StringIO()
    headers = list(rows[0].keys()) if rows else ['No data']
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    else:
        writer.writerow({'No data': ''})
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}.csv'})


def _export_xlsx(filename, rows):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    headers = list(rows[0].keys()) if rows else ['No data']
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header, '') for header in headers])
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
    )


def _overview_search_results(query):
    if not query:
        return []
    like = f'%{query}%'
    results = []
    for client in PMClient.query.filter(PMClient.name.ilike(like)).limit(5).all():
        results.append({'label': client.name, 'meta': 'Client', 'href': url_for('crm_pm.list_clients')})
    for project in PMProject.query.filter(PMProject.name.ilike(like)).limit(5).all():
        results.append({'label': project.name, 'meta': f'Project · {project.client_name}', 'href': url_for('crm_pm.project_detail', id=project.id)})
    for task in PMTask.query.filter(PMTask.description.ilike(like)).limit(5).all():
        results.append({'label': task.description, 'meta': f'Task · {task.task_id_code or "No ID"}', 'href': url_for('crm_pm.project_detail', id=task.project_id)})
    for invoice in PMInvoice.query.filter(PMInvoice.invoice_number.ilike(like)).limit(5).all():
        results.append({'label': invoice.invoice_number, 'meta': 'Invoice', 'href': url_for('crm_pm.invoices_list')})
    return results[:10]


@crm_pm.route('/export/<section>.<fmt>')
@login_required
def export_section(section, fmt):
    rows = _serialize_rows(section)
    filename = f'pm_{section}_{date.today().isoformat()}'
    if fmt == 'csv':
        return _export_csv(filename, rows)
    if fmt == 'xlsx':
        try:
            return _export_xlsx(filename, rows)
        except ModuleNotFoundError:
            flash('XLSX export requires openpyxl. CSV export is available now.', 'warning')
            return redirect(request.referrer or url_for('crm_pm.overview'))
    flash('Unsupported export format.', 'warning')
    return redirect(request.referrer or url_for('crm_pm.overview'))


# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/')
@login_required
def overview():
    projects = PMProject.query.order_by(PMProject.created_at.desc()).all()
    clients = PMClient.query.order_by(PMClient.name).all()
    active_projects = [p for p in projects if _normalize_project_status(p.status) == 'active']
    total_outstanding = sum(p.balance for p in projects)
    total_revenue = sum(p.paid for p in projects)
    monday, sunday = _week_bounds()
    week_tasks = (PMTask.query
                  .filter(PMTask.due_date.isnot(None))
                  .filter(PMTask.due_date >= datetime.combine(monday, datetime.min.time()))
                  .filter(PMTask.due_date <= datetime.combine(sunday, datetime.max.time()))
                  .filter(PMTask.status != 'completed')
                  .order_by(PMTask.due_date, PMTask.id)
                  .all())
    today_focus = (PMDailyFocus.query
                   .filter_by(date=date.today())
                   .order_by(PMDailyFocus.id)
                   .all())
    recent_payments = PMPayment.query.order_by(PMPayment.date.desc(), PMPayment.id.desc()).limit(5).all()
    recent_expenses = PMExpense.query.order_by(PMExpense.date.desc(), PMExpense.id.desc()).limit(5).all()
    global_query = request.args.get('q', '').strip()

    return render_template('admin/pm_overview.html',
                           clients=clients,
                           active_projects=active_projects,
                           total_outstanding=total_outstanding,
                           total_revenue=total_revenue,
                           week_tasks=week_tasks,
                           today_focus=today_focus,
                           recent_payments=recent_payments,
                           recent_expenses=recent_expenses,
                           today=date.today(),
                           global_query=global_query,
                           search_results=_overview_search_results(global_query))


# ─────────────────────────────────────────────────────────────────────────────
# 2. CLIENTS & PROJECTS
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/clients')
@login_required
def list_clients():
    clients  = PMClient.query.order_by(PMClient.name).all()
    projects = PMProject.query.order_by(PMProject.created_at.desc()).all()
    return render_template('admin/pm_clients.html',
                           clients=clients, pm_projects=projects)


@crm_pm.route('/clients/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_client():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        if not name:
            flash('Client name is required.', 'danger')
            return render_template('admin/pm_client_form.html', client=None)
        client = PMClient(
            client_id_code=f'{(PMClient.query.count() + 1):03d}',
            name=name,
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Client "{client.name}" added.', 'success')
        return redirect(url_for('crm_pm.list_clients'))
    return render_template('admin/pm_client_form.html', client=None)


@crm_pm.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_client(id):
    client = PMClient.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Client name is required.', 'danger')
            return render_template('admin/pm_client_form.html', client=client)
        client.name  = name
        client.email = request.form.get('email', '').strip()
        client.phone = request.form.get('phone', '').strip()
        client.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Client "{client.name}" updated.', 'success')
        return redirect(url_for('crm_pm.list_clients'))
    return render_template('admin/pm_client_form.html', client=client)


@crm_pm.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_client(id):
    client = PMClient.query.get_or_404(id)
    project_ids = [project.id for project in client.pm_projects]
    linked_tasks = PMTask.query.filter(PMTask.project_id.in_(project_ids)).count() if project_ids else 0
    linked_payments = PMPayment.query.filter(PMPayment.project_id.in_(project_ids)).count() if project_ids else 0
    linked_invoices = PMInvoice.query.filter(PMInvoice.project_id.in_(project_ids)).count() if project_ids else 0
    if linked_tasks or linked_payments or linked_invoices:
        flash('This client cannot be deleted until linked tasks, payments, and invoices are cleared.', 'warning')
        return redirect(url_for('crm_pm.list_clients'))
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted.', 'success')
    return redirect(url_for('crm_pm.list_clients'))


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROJECTS (CRUD)
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/projects/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_project():
    clients = PMClient.query.order_by(PMClient.name).all()
    selected_client_id = request.args.get('client_id', type=int) or request.form.get('client_id', type=int)
    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        name      = request.form.get('name', '').strip()
        if not name or not client_id:
            flash('Client and project name are required.', 'danger')
            return render_template('admin/pm_project_form.html', pm_project=None, clients=clients, selected_client_id=selected_client_id)
        project = PMProject(
            client_id=client_id,
            name=name,
            status=_normalize_project_status(request.form.get('status', 'active')),
            budget=request.form.get('budget', type=float),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(project)
        db.session.commit()
        flash(f'Project "{project.name}" created.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project.id))
    return render_template('admin/pm_project_form.html', pm_project=None, clients=clients, selected_client_id=selected_client_id)


@crm_pm.route('/projects/<int:id>')
@login_required
def project_detail(id):
    project  = PMProject.query.get_or_404(id)
    tasks    = PMTask.query.filter_by(project_id=id).order_by(PMTask.due_date, PMTask.id).all()
    payments = PMPayment.query.filter_by(project_id=id).order_by(PMPayment.date.desc()).all()
    invoices = PMInvoice.query.filter_by(project_id=id).order_by(PMInvoice.date.desc()).all()
    expenses = PMExpense.query.filter_by(project_id=id).order_by(PMExpense.date.desc()).all()

    # Daily focus entries for this project
    task_ids = [t.id for t in tasks]
    focus_entries = (PMDailyFocus.query
                     .filter(PMDailyFocus.task_id.in_(task_ids))
                     .order_by(PMDailyFocus.date.desc())
                     .all()) if task_ids else []

    # Task logs for this project
    logs = (PMTaskLog.query
            .filter(PMTaskLog.task_id.in_(task_ids))
            .order_by(PMTaskLog.date.desc())
            .all()) if task_ids else []

    # Profitability
    revenue  = project.paid
    exp_total = sum(e.cost for e in expenses if e.cost) or 0.0
    net_profit = revenue - exp_total
    profit_margin = (net_profit / revenue * 100) if revenue else 0.0

    completed = sum(1 for t in tasks if _normalize_task_status(t.status) == 'completed')
    total_actual_hours = sum(
        float(log.actual_time) for log in logs
        if log.actual_time and str(log.actual_time).replace('.', '', 1).isdigit()
    )

    return render_template('admin/pm_project_detail.html',
                           pm_project=project,
                           tasks=tasks,
                           payments=payments,
                           invoices=invoices,
                           expenses=expenses,
                           focus_entries=focus_entries,
                           logs=logs,
                           completed_tasks=completed,
                           total_tasks=len(tasks),
                           revenue=revenue,
                           exp_total=exp_total,
                           net_profit=net_profit,
                           profit_margin=profit_margin,
                           total_actual_hours=total_actual_hours)


@crm_pm.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_project(id):
    project = PMProject.query.get_or_404(id)
    clients = PMClient.query.order_by(PMClient.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Project name is required.', 'danger')
            return render_template('admin/pm_project_form.html', pm_project=project, clients=clients, selected_client_id=project.client_id)
        project.client_id = request.form.get('client_id', type=int)
        project.name      = name
        project.status    = _normalize_project_status(request.form.get('status', project.status))
        project.budget    = request.form.get('budget', type=float)
        project.notes     = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Project "{project.name}" updated.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project.id))
    return render_template('admin/pm_project_form.html', pm_project=project, clients=clients, selected_client_id=project.client_id)


@crm_pm.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_project(id):
    project = PMProject.query.get_or_404(id)
    if project.tasks or project.payments or project.invoices or PMExpense.query.filter_by(project_id=project.id).first():
        flash('This project cannot be deleted until its tasks, payments, invoices, and expenses are cleared.', 'warning')
        return redirect(url_for('crm_pm.project_detail', id=project.id))
    name = project.name
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{name}" deleted.', 'success')
    return redirect(url_for('crm_pm.list_clients'))


# ─────────────────────────────────────────────────────────────────────────────
# 4. TASK MASTER
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/tasks')
@login_required
def task_master():
    tasks    = (PMTask.query
                .join(PMProject)
                .join(PMClient)
                .order_by(PMTask.due_date, PMTask.id)
                .all())
    clients  = PMClient.query.order_by(PMClient.name).all()
    projects = PMProject.query.order_by(PMProject.name).all()
    return render_template('admin/pm_task_master.html',
                           tasks=tasks, clients=clients, pm_projects=projects)


@crm_pm.route('/tasks/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_task():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None
    projects   = PMProject.query.order_by(PMProject.name).all()

    if request.method == 'POST':
        description     = request.form.get('description', '').strip()
        pid             = request.form.get('project_id', type=int)
        if not description or not pid:
            flash('Project and task description are required.', 'danger')
            return render_template('admin/pm_task_form.html', task=None, project=project, projects=projects)

        # Auto-generate task_id_code: [ClientID_padded]-[seq]
        proj = PMProject.query.get(pid)
        seq  = PMTask.query.filter_by(project_id=pid).count() + 1
        code = f'{proj.client_id:03d}-{seq:03d}' if proj else None

        task = PMTask(
            project_id=pid,
            task_id_code=code,
            description=description,
            status=_normalize_task_status(request.form.get('status', 'not_started')),
            priority=request.form.get('priority', '3/5').strip(),
            estimated_hours=request.form.get('estimated_hours', type=float),
            notes=request.form.get('notes', '').strip(),
            due_date=_parse_date(request.form.get('due_date')),
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=pid))

    return render_template('admin/pm_task_form.html', task=None, project=project, projects=projects)


@crm_pm.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_task(id):
    task     = PMTask.query.get_or_404(id)
    projects = PMProject.query.order_by(PMProject.name).all()

    if request.method == 'POST':
        task.project_id       = request.form.get('project_id', type=int) or task.project_id
        task.description     = request.form.get('description', '').strip()
        task.status          = _normalize_task_status(request.form.get('status', task.status))
        task.priority        = request.form.get('priority', task.priority).strip()
        task.estimated_hours = request.form.get('estimated_hours', type=float)
        task.notes           = request.form.get('notes', '').strip()
        task.due_date        = _parse_date(request.form.get('due_date'))
        db.session.commit()
        flash('Task updated.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=task.project_id))
    return render_template('admin/pm_task_form.html', task=task, project=task.project, projects=projects)


@crm_pm.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_task(id):
    task = PMTask.query.get_or_404(id)
    if task.daily_focus_entries or task.logs:
        flash('This task cannot be deleted until its Daily Focus and Task Log entries are removed.', 'warning')
        return redirect(url_for('crm_pm.project_detail', id=task.project_id))
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('crm_pm.project_detail', id=project_id))


@crm_pm.route('/tasks/<int:id>/status', methods=['POST'])
@login_required
@_role_required('pm')
def update_task_status(id):
    task = PMTask.query.get_or_404(id)
    s = request.form.get('status', '').strip()
    if s:
        task.status = _normalize_task_status(s)
        db.session.commit()
    return redirect(url_for('crm_pm.project_detail', id=task.project_id))


# ─────────────────────────────────────────────────────────────────────────────
# 5. DAILY FOCUS
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/daily-focus')
@login_required
def daily_focus():
    entries = (PMDailyFocus.query
               .order_by(PMDailyFocus.date.desc(), PMDailyFocus.id)
               .all())
    today = date.today()
    hours_by_day = {}
    for entry in entries:
        raw = (entry.est_time or '').lower().replace('hours', '').replace('hour', '').replace('hrs', '').replace('hr', '').strip()
        try:
            hours_by_day[entry.date.isoformat()] = hours_by_day.get(entry.date.isoformat(), 0) + float(raw)
        except ValueError:
            hours_by_day.setdefault(entry.date.isoformat(), 0)
    return render_template('admin/pm_daily_focus.html', entries=entries, today=today, hours_by_day=hours_by_day)


@crm_pm.route('/daily-focus/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_focus():
    tasks = (PMTask.query
             .join(PMProject)
             .filter(PMTask.status != 'completed')
             .order_by(PMProject.name, PMTask.id)
             .all())
    default_date = request.args.get('date', date.today().isoformat())

    if request.method == 'POST':
        focus_date = _parse_date_only(request.form.get('date'))
        task_id    = request.form.get('task_id', type=int)
        if not focus_date or not task_id:
            flash('Date and task are required.', 'danger')
            return render_template('admin/pm_daily_focus_form.html',
                                   entry=None, tasks=tasks, default_date=default_date)
        entry = PMDailyFocus(
            date=focus_date,
            task_id=task_id,
            est_time=request.form.get('est_time', '').strip(),
            status=_normalize_task_status(request.form.get('status', 'not_started')),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(entry)
        db.session.commit()
        flash('Focus entry added.', 'success')
        return redirect(url_for('crm_pm.daily_focus'))

    return render_template('admin/pm_daily_focus_form.html',
                           entry=None, tasks=tasks, default_date=default_date)


@crm_pm.route('/daily-focus/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_focus(id):
    entry = PMDailyFocus.query.get_or_404(id)
    tasks = (PMTask.query
             .join(PMProject)
             .order_by(PMProject.name, PMTask.id)
             .all())

    if request.method == 'POST':
        entry.date     = _parse_date_only(request.form.get('date')) or entry.date
        entry.task_id  = request.form.get('task_id', type=int) or entry.task_id
        entry.est_time = request.form.get('est_time', '').strip()
        entry.status   = _normalize_task_status(request.form.get('status', entry.status))
        entry.notes    = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Entry updated.', 'success')
        return redirect(url_for('crm_pm.daily_focus'))

    return render_template('admin/pm_daily_focus_form.html',
                           entry=entry, tasks=tasks,
                           default_date=entry.date.isoformat() if entry.date else '')


@crm_pm.route('/daily-focus/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_focus(id):
    entry = PMDailyFocus.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.', 'success')
    return redirect(url_for('crm_pm.daily_focus'))


# ─────────────────────────────────────────────────────────────────────────────
# 6. TASK LOG
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/task-log')
@login_required
def task_log():
    logs = (PMTaskLog.query
            .order_by(PMTaskLog.date.desc(), PMTaskLog.id.desc())
            .all())
    return render_template('admin/pm_task_log.html', logs=logs)


@crm_pm.route('/tasks/<int:id>/log', methods=['GET', 'POST'])
@login_required
@_role_required('pm', 'freelancer')
def log_task_time(id):
    task = PMTask.query.get_or_404(id)
    if request.method == 'POST':
        date_val     = _parse_date(request.form.get('date'))
        actual_hours = request.form.get('actual_hours', '').strip()
        raw_status   = request.form.get('status', '').strip()
        status_upd   = _normalize_task_status(raw_status) if raw_status else ''
        notes        = request.form.get('notes', '').strip()
        if not date_val or not actual_hours:
            flash('Date and hours are required.', 'danger')
            return render_template('admin/pm_log_form.html', task=task, log=None)
        log_entry = PMTaskLog(
            task_id=task.id,
            date=date_val,
            actual_time=actual_hours,
            status=status_upd or None,
            notes=notes,
        )
        db.session.add(log_entry)
        if status_upd:
            task.status = status_upd
        db.session.commit()
        flash('Work log saved.', 'success')
        return redirect(url_for('crm_pm.task_log'))
    return render_template('admin/pm_log_form.html', task=task, log=None)


@crm_pm.route('/logs/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('freelancer')
def edit_log(id):
    log = PMTaskLog.query.get_or_404(id)
    task = log.task
    if request.method == 'POST':
        log.date = _parse_date(request.form.get('date')) or log.date
        log.actual_time = request.form.get('actual_hours', '').strip()
        raw_status = request.form.get('status', '').strip()
        log.status = _normalize_task_status(raw_status) if raw_status else None
        log.notes = request.form.get('notes', '').strip()
        if log.status:
            task.status = log.status
        db.session.commit()
        flash('Work log updated.', 'success')
        return redirect(url_for('crm_pm.task_log'))
    return render_template('admin/pm_log_form.html', task=task, log=log)


@crm_pm.route('/logs/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('freelancer')
def delete_log(id):
    log = PMTaskLog.query.get_or_404(id)
    db.session.delete(log)
    db.session.commit()
    flash('Work log deleted.', 'success')
    return redirect(url_for('crm_pm.task_log'))


# ─────────────────────────────────────────────────────────────────────────────
# 7. PAYMENTS
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/payments')
@login_required
@_role_required('pm')
def payments_list():
    payments       = PMPayment.query.order_by(PMPayment.date.desc()).all()
    total_received = sum(p.amount for p in payments if p.amount) or 0.0
    return render_template('admin/pm_payments_list.html',
                           payments=payments, total_received=total_received)


@crm_pm.route('/payments/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_payment():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None
    invoices   = PMInvoice.query.filter_by(project_id=project_id).all() if project_id else []
    projects   = PMProject.query.order_by(PMProject.name).all()

    if request.method == 'POST':
        pid      = request.form.get('project_id', type=int)
        amount   = request.form.get('amount', type=float)
        date_val = _parse_date(request.form.get('date'))
        if not amount or not pid or not date_val:
            flash('Project, date, and amount are required.', 'danger')
            return render_template('admin/pm_payment_form.html',
                                   project=project, project_id=project_id,
                                   invoices=invoices, projects=projects)
        proj = PMProject.query.get_or_404(pid)
        invoice = PMInvoice.query.get(request.form.get('invoice_id', type=int)) if request.form.get('invoice_id', type=int) else None
        payment = PMPayment(
            project_id=pid,
            amount=amount,
            payment_method=request.form.get('payment_method', '').strip(),
            date=date_val,
            receipt_id=request.form.get('receipt_id', '').strip() or _project_receipt_id(proj, invoice),
            invoice_id=invoice.id if invoice else None,
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(payment)
        db.session.commit()
        flash(f'Payment of ${amount:,.2f} recorded.', 'success')
        return redirect(url_for('crm_pm.payments_list'))

    return render_template('admin/pm_payment_form.html',
                           project=project, project_id=project_id,
                           invoices=invoices, projects=projects)


@crm_pm.route('/payments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_payment(id):
    payment  = PMPayment.query.get_or_404(id)
    invoices = PMInvoice.query.filter_by(project_id=payment.project_id).all()
    projects = PMProject.query.order_by(PMProject.name).all()

    if request.method == 'POST':
        payment.project_id      = request.form.get('project_id', type=int) or payment.project_id
        payment.amount         = request.form.get('amount', type=float)
        payment.payment_method = request.form.get('payment_method', '').strip()
        payment.date           = _parse_date(request.form.get('date')) or payment.date
        payment.receipt_id     = request.form.get('receipt_id', '').strip() or None
        payment.invoice_id     = request.form.get('invoice_id', type=int) or None
        payment.notes          = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Payment updated.', 'success')
        return redirect(url_for('crm_pm.payments_list'))

    return render_template('admin/pm_payment_form.html', payment=payment,
                           project_id=payment.project_id,
                           invoices=invoices, projects=projects)


@crm_pm.route('/payments/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_payment(id):
    payment = PMPayment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    flash('Payment deleted.', 'success')
    return redirect(url_for('crm_pm.payments_list'))


# ─────────────────────────────────────────────────────────────────────────────
# 8. INVOICES
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/invoices')
@login_required
@_role_required('pm')
def invoices_list():
    invoices        = PMInvoice.query.order_by(PMInvoice.date.desc()).all()
    total_invoiced  = sum(i.amount for i in invoices if i.amount) or 0.0
    total_paid      = sum(i.amount for i in invoices if i.payment_status == 'paid' and i.amount) or 0.0
    total_outstanding = total_invoiced - total_paid
    return render_template('admin/pm_invoices_list.html',
                           invoices=invoices,
                           total_invoiced=total_invoiced,
                           total_paid=total_paid,
                           total_outstanding=total_outstanding)


@crm_pm.route('/invoices/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_invoice():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None
    tasks      = PMTask.query.filter_by(project_id=project_id).all() if project_id else []
    projects   = PMProject.query.order_by(PMProject.name).all()

    last = PMInvoice.query.order_by(PMInvoice.id.desc()).first()
    if project and tasks:
        suggested = f'{project.client_id:03d}-{tasks[0].task_id_code}-IV'
    elif project:
        suggested = f'{project.client_id:03d}-GEN-IV'
    else:
        suggested = f'INV-{datetime.now().year}-{((last.id + 1) if last else 1):03d}'

    if request.method == 'POST':
        pid    = request.form.get('project_id', type=int)
        amount = request.form.get('amount', type=float)
        date_v = _parse_date(request.form.get('date'))
        if not amount or not pid or not date_v:
            flash('Project, date, and amount are required.', 'danger')
            return render_template('admin/pm_invoice_form.html',
                                   project=project, project_id=project_id,
                                   tasks=tasks, projects=projects,
                                   suggested_invoice_number=suggested)
        invoice = PMInvoice(
            project_id=pid,
            invoice_number=request.form.get('invoice_number', '').strip() or suggested,
            amount=amount,
            date=date_v,
            payment_status=_normalize_invoice_status(request.form.get('payment_status', 'unpaid')),
            task_id=request.form.get('task_id', type=int) or None,
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(invoice)
        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} created.', 'success')
        return redirect(url_for('crm_pm.invoices_list'))

    return render_template('admin/pm_invoice_form.html',
                           project=project, project_id=project_id,
                           tasks=tasks, projects=projects,
                           suggested_invoice_number=suggested)


@crm_pm.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_invoice(id):
    invoice  = PMInvoice.query.get_or_404(id)
    tasks    = PMTask.query.filter_by(project_id=invoice.project_id).all()
    projects = PMProject.query.order_by(PMProject.name).all()

    if request.method == 'POST':
        invoice.project_id      = request.form.get('project_id', type=int) or invoice.project_id
        invoice.invoice_number = request.form.get('invoice_number', '').strip()
        invoice.amount         = request.form.get('amount', type=float)
        invoice.date           = _parse_date(request.form.get('date')) or invoice.date
        invoice.payment_status = _normalize_invoice_status(request.form.get('payment_status', invoice.payment_status))
        invoice.task_id        = request.form.get('task_id', type=int) or None
        invoice.notes          = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Invoice updated.', 'success')
        return redirect(url_for('crm_pm.invoices_list'))

    return render_template('admin/pm_invoice_form.html', invoice=invoice,
                           project_id=invoice.project_id, tasks=tasks, projects=projects)


@crm_pm.route('/invoices/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_invoice(id):
    invoice = PMInvoice.query.get_or_404(id)
    if PMPayment.query.filter_by(invoice_id=invoice.id).first():
        flash('This invoice cannot be deleted while payments are linked to it.', 'warning')
        return redirect(url_for('crm_pm.invoices_list'))
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted.', 'success')
    return redirect(url_for('crm_pm.invoices_list'))


# ─────────────────────────────────────────────────────────────────────────────
# 9. EXPENSES
# ─────────────────────────────────────────────────────────────────────────────

@crm_pm.route('/expenses')
@login_required
@_role_required('pm')
def list_expenses():
    expenses = PMExpense.query.order_by(PMExpense.date.desc()).all()
    total_expenses = sum(e.cost for e in expenses if e.cost) or 0.0
    now = datetime.now()
    month_expenses = sum(
        e.cost for e in expenses
        if e.cost and e.date and e.date.year == now.year and e.date.month == now.month
    ) or 0.0
    months_seen = sorted({e.date.strftime('%Y-%m') for e in expenses if e.date}, reverse=True)
    monthly_data = {}
    for expense in expenses:
        if expense.date:
            key = expense.date.strftime('%Y-%m')
            monthly_data[key] = monthly_data.get(key, 0) + (expense.cost or 0)
    return render_template('admin/pm_expenses_list.html',
                           expenses=expenses,
                           total_expenses=total_expenses,
                           month_expenses=month_expenses,
                           available_months=months_seen,
                           chart_data=[{'month': month, 'total': total} for month, total in sorted(monthly_data.items())])


@crm_pm.route('/expenses/new', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def new_expense():
    pm_projects = PMProject.query.order_by(PMProject.name).all()
    if request.method == 'POST':
        item     = request.form.get('item', '').strip()
        cost     = request.form.get('cost', type=float)
        date_val = _parse_date(request.form.get('date'))
        if not item or not cost or not date_val:
            flash('Date, item, and cost are required.', 'danger')
            return render_template('admin/pm_expense_form.html', expense=None, pm_projects=pm_projects)
        expense = PMExpense(
            item=item, cost=cost, date=date_val,
            category=request.form.get('category', '').strip() or None,
            notes=request.form.get('notes', '').strip() or None,
            project_id=request.form.get('project_id', type=int) or None,
        )
        db.session.add(expense)
        db.session.commit()
        flash(f'Expense recorded.', 'success')
        return redirect(url_for('crm_pm.list_expenses'))
    return render_template('admin/pm_expense_form.html', expense=None, pm_projects=pm_projects)


@crm_pm.route('/expenses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@_role_required('pm')
def edit_expense(id):
    expense     = PMExpense.query.get_or_404(id)
    pm_projects = PMProject.query.order_by(PMProject.name).all()
    if request.method == 'POST':
        expense.item       = request.form.get('item', '').strip()
        expense.cost       = request.form.get('cost', type=float)
        expense.date       = _parse_date(request.form.get('date')) or expense.date
        expense.category   = request.form.get('category', '').strip() or None
        expense.notes      = request.form.get('notes', '').strip() or None
        expense.project_id = request.form.get('project_id', type=int) or None
        db.session.commit()
        flash('Expense updated.', 'success')
        return redirect(url_for('crm_pm.list_expenses'))
    return render_template('admin/pm_expense_form.html', expense=expense, pm_projects=pm_projects)


@crm_pm.route('/expenses/<int:id>/delete', methods=['POST'])
@login_required
@_role_required('pm')
def delete_expense(id):
    expense = PMExpense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('crm_pm.list_expenses'))
