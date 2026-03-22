from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import ActiveProject

crm_active_projects = Blueprint('crm_active_projects', __name__, url_prefix='/admin/crm/active-projects')


@crm_active_projects.route('/')
@login_required
def list_active_projects():
    projects = ActiveProject.query.order_by(ActiveProject.created_at.desc()).all()
    return render_template('admin/active_projects_list.html', projects=projects)


@crm_active_projects.route('/new', methods=['GET', 'POST'])
@login_required
def new_active_project():
    if request.method == 'POST':
        project_name  = request.form.get('project_name', '').strip()
        client_name   = request.form.get('client_name', '').strip()
        is_private    = request.form.get('is_private') == 'on'
        is_anonymous  = request.form.get('is_anonymous') == 'on'
        expected_finish = request.form.get('expected_finish') or None
        status        = request.form.get('status', 'active').strip()
        source        = request.form.get('source', '').strip()
        notes         = request.form.get('notes', '').strip()

        if not project_name:
            flash('Project name is required.', 'danger')
            return render_template('admin/active_project_form.html', project=None)

        project = ActiveProject(
            project_name=project_name,
            client_name=client_name,
            is_private=is_private,
            is_anonymous=is_anonymous,
            expected_finish=expected_finish,
            status=status,
            source=source,
            notes=notes,
        )
        db.session.add(project)
        db.session.commit()
        flash(f'Active project "{project.project_name}" created.', 'success')
        return redirect(url_for('crm_active_projects.list_active_projects'))

    return render_template('admin/active_project_form.html', project=None)


@crm_active_projects.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_active_project(id):
    project = ActiveProject.query.get_or_404(id)

    if request.method == 'POST':
        project_name  = request.form.get('project_name', '').strip()
        if not project_name:
            flash('Project name is required.', 'danger')
            return render_template('admin/active_project_form.html', project=project)

        project.project_name  = project_name
        project.client_name   = request.form.get('client_name', '').strip()
        project.is_private    = request.form.get('is_private') == 'on'
        project.is_anonymous  = request.form.get('is_anonymous') == 'on'
        project.expected_finish = request.form.get('expected_finish') or None
        project.status        = request.form.get('status', project.status).strip()
        project.source        = request.form.get('source', '').strip()
        project.notes         = request.form.get('notes', '').strip()

        db.session.commit()
        flash(f'Project "{project.project_name}" updated.', 'success')
        return redirect(url_for('crm_active_projects.list_active_projects'))

    return render_template('admin/active_project_form.html', project=project)


@crm_active_projects.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_active_project(id):
    project = ActiveProject.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{project.project_name}" deleted.', 'success')
    return redirect(url_for('crm_active_projects.list_active_projects'))
