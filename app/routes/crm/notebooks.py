from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Notebook

crm_notebooks = Blueprint('crm_notebooks', __name__, template_folder='../../../templates')


@crm_notebooks.route('/')
@login_required
def list_notebooks():
    notebooks = (
        db.session.query(Notebook)
        .order_by(Notebook.sort_order.asc(), Notebook.created_at.desc())
        .all()
    )
    return render_template('admin/notebooks_list.html', notebooks=notebooks)


@crm_notebooks.route('/new', methods=['GET', 'POST'])
@login_required
def new_notebook():
    if request.method == 'POST':
        notebook = Notebook(
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip() or None,
            tools_used=request.form.get('tools_used', '').strip() or None,
            colab_url=request.form.get('colab_url', '').strip(),
            cover_image_url=request.form.get('cover_image_url', '').strip() or None,
            category=request.form.get('category', '').strip() or None,
            source=request.form.get('source', 'personal').strip(),
            is_visible=bool(request.form.get('is_visible')),
            sort_order=int(request.form.get('sort_order') or 0),
        )
        db.session.add(notebook)
        db.session.commit()
        flash('Notebook created successfully.', 'success')
        return redirect(url_for('crm_notebooks.list_notebooks'))

    return render_template('admin/notebook_form.html', notebook=None)


@crm_notebooks.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_notebook(id):
    notebook = db.session.get(Notebook, id)
    if notebook is None:
        flash('Notebook not found.', 'danger')
        return redirect(url_for('crm_notebooks.list_notebooks'))

    if request.method == 'POST':
        notebook.title = request.form.get('title', '').strip()
        notebook.description = request.form.get('description', '').strip() or None
        notebook.tools_used = request.form.get('tools_used', '').strip() or None
        notebook.colab_url = request.form.get('colab_url', '').strip()
        notebook.cover_image_url = request.form.get('cover_image_url', '').strip() or None
        notebook.category = request.form.get('category', '').strip() or None
        notebook.source = request.form.get('source', 'personal').strip()
        notebook.is_visible = bool(request.form.get('is_visible'))
        notebook.sort_order = int(request.form.get('sort_order') or 0)
        db.session.commit()
        flash('Notebook updated successfully.', 'success')
        return redirect(url_for('crm_notebooks.list_notebooks'))

    return render_template('admin/notebook_form.html', notebook=notebook)


@crm_notebooks.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_notebook(id):
    notebook = db.session.get(Notebook, id)
    if notebook is None:
        flash('Notebook not found.', 'danger')
        return redirect(url_for('crm_notebooks.list_notebooks'))

    db.session.delete(notebook)
    db.session.commit()
    flash('Notebook deleted.', 'success')
    return redirect(url_for('crm_notebooks.list_notebooks'))
