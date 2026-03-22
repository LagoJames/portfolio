from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import PMClient, PMProject, PMTask, PMTaskLog, PMPayment, PMInvoice, PMExpense

crm_pm = Blueprint('crm_pm', __name__, url_prefix='/admin/crm/pm')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@crm_pm.route('/')
@login_required
def dashboard():
    clients  = PMClient.query.order_by(PMClient.name).all()
    projects = PMProject.query.order_by(PMProject.created_at.desc()).all()
    return render_template('admin/pm_dashboard.html', clients=clients, projects=projects)


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@crm_pm.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name:
            flash('Client name is required.', 'danger')
            return render_template('admin/pm_client_form.html', client=None)

        client = PMClient(name=name, email=email, phone=phone, notes=notes)
        db.session.add(client)
        db.session.commit()
        flash(f'Client "{client.name}" added.', 'success')
        return redirect(url_for('crm_pm.dashboard'))

    return render_template('admin/pm_client_form.html', client=None)


@crm_pm.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('crm_pm.dashboard'))

    return render_template('admin/pm_client_form.html', client=client)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@crm_pm.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    clients = PMClient.query.order_by(PMClient.name).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        name      = request.form.get('name', '').strip()
        status    = request.form.get('status', 'active').strip()
        budget    = request.form.get('budget', type=float)
        notes     = request.form.get('notes', '').strip()

        if not name or not client_id:
            flash('Client and project name are required.', 'danger')
            return render_template('admin/pm_project_form.html', project=None, clients=clients)

        project = PMProject(
            client_id=client_id,
            name=name,
            status=status,
            budget=budget,
            notes=notes,
        )
        db.session.add(project)
        db.session.commit()
        flash(f'Project "{project.name}" created.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project.id))

    return render_template('admin/pm_project_form.html', project=None, clients=clients)


@crm_pm.route('/projects/<int:id>')
@login_required
def project_detail(id):
    project  = PMProject.query.get_or_404(id)
    tasks    = PMTask.query.filter_by(project_id=id).order_by(PMTask.created_at).all()
    payments = PMPayment.query.filter_by(project_id=id).order_by(PMPayment.date.desc()).all()
    invoices = PMInvoice.query.filter_by(project_id=id).order_by(PMInvoice.issued_date.desc()).all()
    return render_template(
        'admin/pm_project_detail.html',
        project=project,
        tasks=tasks,
        payments=payments,
        invoices=invoices,
    )


@crm_pm.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = PMProject.query.get_or_404(id)
    clients = PMClient.query.order_by(PMClient.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Project name is required.', 'danger')
            return render_template('admin/pm_project_form.html', project=project, clients=clients)

        project.client_id = request.form.get('client_id', type=int)
        project.name      = name
        project.status    = request.form.get('status', project.status).strip()
        project.budget    = request.form.get('budget', type=float)
        project.notes     = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Project "{project.name}" updated.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project.id))

    return render_template('admin/pm_project_form.html', project=project, clients=clients)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@crm_pm.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        status      = request.form.get('status', 'todo').strip()
        due_date    = request.form.get('due_date') or None

        if not title or not project_id:
            flash('Project and task title are required.', 'danger')
            return render_template('admin/pm_task_form.html', task=None, project=project)

        task = PMTask(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            due_date=due_date,
        )
        db.session.add(task)
        db.session.commit()
        flash(f'Task "{task.title}" added.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project_id))

    return render_template('admin/pm_task_form.html', task=None, project=project)


@crm_pm.route('/tasks/<int:id>/status', methods=['POST'])
@login_required
def update_task_status(id):
    task       = PMTask.query.get_or_404(id)
    new_status = request.form.get('status', '').strip()
    if new_status:
        task.status = new_status
        db.session.commit()
        flash(f'Task status updated to "{new_status}".', 'success')
    else:
        flash('No status provided.', 'warning')
    return redirect(url_for('crm_pm.project_detail', id=task.project_id))


@crm_pm.route('/tasks/<int:id>/log', methods=['GET', 'POST'])
@login_required
def log_task_time(id):
    task = PMTask.query.get_or_404(id)

    if request.method == 'POST':
        hours   = request.form.get('hours', type=float)
        notes   = request.form.get('notes', '').strip()
        log_date = request.form.get('log_date') or None

        if not hours or hours <= 0:
            flash('A positive number of hours is required.', 'danger')
            return render_template('admin/pm_log_form.html', task=task)

        log_entry = PMTaskLog(task_id=task.id, hours=hours, notes=notes, date=log_date)
        db.session.add(log_entry)
        db.session.commit()
        flash(f'{hours}h logged to "{task.title}".', 'success')
        return redirect(url_for('crm_pm.project_detail', id=task.project_id))

    return render_template('admin/pm_log_form.html', task=task)


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@crm_pm.route('/payments/new', methods=['GET', 'POST'])
@login_required
def new_payment():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None

    if request.method == 'POST':
        amount  = request.form.get('amount', type=float)
        method  = request.form.get('method', '').strip()
        date    = request.form.get('date') or None
        notes   = request.form.get('notes', '').strip()

        if not amount or not project_id:
            flash('Project and payment amount are required.', 'danger')
            return render_template('admin/pm_payment_form.html', project=project)

        payment = PMPayment(
            project_id=project_id,
            amount=amount,
            method=method,
            date=date,
            notes=notes,
        )
        db.session.add(payment)
        db.session.commit()
        flash(f'Payment of ${amount:,.2f} recorded.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project_id))

    return render_template('admin/pm_payment_form.html', project=project)


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

@crm_pm.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    project_id = request.args.get('project_id', type=int) or request.form.get('project_id', type=int)
    project    = PMProject.query.get_or_404(project_id) if project_id else None

    if request.method == 'POST':
        invoice_number = request.form.get('invoice_number', '').strip()
        amount         = request.form.get('amount', type=float)
        issued_date    = request.form.get('issued_date') or None
        due_date       = request.form.get('due_date') or None
        status         = request.form.get('status', 'unpaid').strip()
        notes          = request.form.get('notes', '').strip()

        if not amount or not project_id:
            flash('Project and invoice amount are required.', 'danger')
            return render_template('admin/pm_invoice_form.html', project=project)

        invoice = PMInvoice(
            project_id=project_id,
            invoice_number=invoice_number,
            amount=amount,
            issued_date=issued_date,
            due_date=due_date,
            status=status,
            notes=notes,
        )
        db.session.add(invoice)
        db.session.commit()
        flash(f'Invoice #{invoice_number or invoice.id} created.', 'success')
        return redirect(url_for('crm_pm.project_detail', id=project_id))

    return render_template('admin/pm_invoice_form.html', project=project)


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@crm_pm.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        amount      = request.form.get('amount', type=float)
        category    = request.form.get('category', '').strip()
        date        = request.form.get('date') or None
        notes       = request.form.get('notes', '').strip()

        if not description or not amount:
            flash('Description and amount are required.', 'danger')
            return render_template('admin/pm_expense_form.html')

        expense = PMExpense(
            description=description,
            amount=amount,
            category=category,
            date=date,
            notes=notes,
        )
        db.session.add(expense)
        db.session.commit()
        flash(f'Expense "${amount:,.2f} — {description}" recorded.', 'success')
        return redirect(url_for('crm_pm.list_expenses'))

    return render_template('admin/pm_expense_form.html')


@crm_pm.route('/expenses')
@login_required
def list_expenses():
    expenses = PMExpense.query.order_by(PMExpense.date.desc()).all()
    return render_template('admin/pm_expenses_list.html', expenses=expenses)
