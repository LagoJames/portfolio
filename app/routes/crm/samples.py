import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

crm_samples = Blueprint('crm_samples', __name__, template_folder='../../../templates')

PAPERS_DIR = os.path.join('app', 'static', 'samples', 'papers')
METADATA_FILE = os.path.join(PAPERS_DIR, 'metadata.json')
ALLOWED_EXTENSIONS = {'docx', 'pdf'}


def _load_metadata():
    if not os.path.exists(METADATA_FILE):
        return []
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)


def _save_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@crm_samples.route('/')
@login_required
def samples_list():
    papers = _load_metadata()
    return render_template('admin/samples_list.html', papers=papers)


@crm_samples.route('/upload', methods=['POST'])
@login_required
def upload_paper():
    f = request.files.get('file')
    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    desc = request.form.get('desc', '').strip()

    if not f or not f.filename:
        flash('No file selected.', 'error')
        return redirect(url_for('crm_samples.samples_list'))

    if not _allowed(f.filename):
        flash('Only .docx and .pdf files are allowed.', 'error')
        return redirect(url_for('crm_samples.samples_list'))

    if not title:
        flash('Title is required.', 'error')
        return redirect(url_for('crm_samples.samples_list'))

    filename = secure_filename(f.filename)
    os.makedirs(PAPERS_DIR, exist_ok=True)
    f.save(os.path.join(PAPERS_DIR, filename))

    papers = _load_metadata()
    # Update if file already exists in metadata, otherwise append
    existing = next((p for p in papers if p['file'] == filename), None)
    if existing:
        existing.update({'title': title, 'category': category, 'desc': desc})
    else:
        papers.append({'file': filename, 'title': title, 'category': category, 'desc': desc})
    _save_metadata(papers)

    flash(f'"{title}" uploaded successfully.', 'success')
    return redirect(url_for('crm_samples.samples_list'))


@crm_samples.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_paper(filename):
    safe = secure_filename(filename)
    path = os.path.join(PAPERS_DIR, safe)
    if os.path.exists(path):
        os.remove(path)

    papers = _load_metadata()
    papers = [p for p in papers if p['file'] != safe]
    _save_metadata(papers)

    flash('Paper deleted.', 'success')
    return redirect(url_for('crm_samples.samples_list'))


@crm_samples.route('/edit/<filename>', methods=['POST'])
@login_required
def edit_paper(filename):
    safe = secure_filename(filename)
    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    desc = request.form.get('desc', '').strip()

    papers = _load_metadata()
    for p in papers:
        if p['file'] == safe:
            p.update({'title': title, 'category': category, 'desc': desc})
            break
    _save_metadata(papers)

    flash('Paper updated.', 'success')
    return redirect(url_for('crm_samples.samples_list'))
