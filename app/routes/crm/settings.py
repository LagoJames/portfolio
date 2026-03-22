import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import Setting

crm_settings = Blueprint('crm_settings', __name__, template_folder='../../../templates')

SETTINGS_KEYS = [
    'display_name',
    'tagline',
    'about_short',
    'contact_email',
    'availability_status',   # available | limited | busy
    'availability_note',
    'stat_projects',
    'stat_earnings',
    'stat_years',
    'stat_papers',
    'github_username',
    'substack_quant_url',
    'substack_jarida_url',
    'upwork_url',
    'linkedin_url',
    'meta_description',
    'google_analytics_id',
    # Upload-backed keys (values stored as relative URL paths)
    'profile_photo_url',
    'cv_url',
]

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_CV_EXTENSIONS = {'pdf', 'doc', 'docx'}


def _allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


def _upload_dir():
    """Return the configured upload folder, falling back to app/static/uploads."""
    return current_app.config.get(
        'UPLOAD_FOLDER',
        os.path.join(current_app.root_path, 'static', 'uploads'),
    )


def _save_upload(file_storage, sub_folder, allowed_exts):
    """
    Validate, save, and return the URL-path for an uploaded file.
    Returns None if file_storage is empty or invalid.
    Raises ValueError with a user-facing message on validation failure.
    """
    if not file_storage or file_storage.filename == '':
        return None

    if not _allowed_file(file_storage.filename, allowed_exts):
        raise ValueError(
            f'File type not allowed. Accepted: {", ".join(sorted(allowed_exts))}'
        )

    filename = secure_filename(file_storage.filename)
    # Prefix with a timestamp to avoid collisions
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    filename = f'{timestamp}_{filename}'

    dest_dir = os.path.join(_upload_dir(), sub_folder)
    os.makedirs(dest_dir, exist_ok=True)

    file_storage.save(os.path.join(dest_dir, filename))
    return f'/static/uploads/{sub_folder}/{filename}'


def _load_settings():
    """Return all Setting rows as a plain dict keyed by Setting.key."""
    rows = db.session.query(Setting).all()
    return {row.key: row.value for row in rows}


def _upsert(key, value):
    """Insert or update a single Setting row."""
    row = db.session.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        db.session.add(row)
    else:
        row.value = value


@crm_settings.route('/', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # --- Handle plain text fields ---
        text_keys = [k for k in SETTINGS_KEYS if k not in ('profile_photo_url', 'cv_url')]
        for key in text_keys:
            value = request.form.get(key, '').strip() or None
            _upsert(key, value)

        # --- Handle profile photo upload ---
        profile_photo = request.files.get('profile_photo')
        try:
            photo_url = _save_upload(profile_photo, 'photos', ALLOWED_IMAGE_EXTENSIONS)
            if photo_url:
                _upsert('profile_photo_url', photo_url)
        except ValueError as exc:
            flash(f'Profile photo: {exc}', 'danger')
            db.session.rollback()
            return redirect(url_for('crm_settings.settings'))

        # --- Handle CV upload ---
        cv_file = request.files.get('cv_file')
        try:
            cv_url = _save_upload(cv_file, 'cv', ALLOWED_CV_EXTENSIONS)
            if cv_url:
                _upsert('cv_url', cv_url)
        except ValueError as exc:
            flash(f'CV file: {exc}', 'danger')
            db.session.rollback()
            return redirect(url_for('crm_settings.settings'))

        db.session.commit()
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('crm_settings.settings'))

    current_settings = _load_settings()
    return render_template('admin/settings.html', settings=current_settings)
