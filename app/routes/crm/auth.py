import bcrypt
from collections import defaultdict, deque
from time import time
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import AdminUser

crm_auth = Blueprint('crm_auth', __name__, template_folder='../../../templates')
_LOGIN_ATTEMPTS = defaultdict(deque)


def _client_ip():
    forwarded = (request.headers.get('X-Forwarded-For') or '').split(',')[0].strip()
    return forwarded or request.remote_addr or 'unknown'


def _prune_attempts(ip, window_seconds):
    now = time()
    attempts = _LOGIN_ATTEMPTS[ip]
    while attempts and now - attempts[0] > window_seconds:
        attempts.popleft()
    return attempts


def _safe_next_url(next_page):
    if not next_page:
        return None
    parsed = urlparse(next_page)
    if parsed.scheme or parsed.netloc:
        return None
    if not next_page.startswith('/'):
        return None
    return next_page


@crm_auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('crm_dashboard.dashboard'))

    if request.method == 'POST':
        ip = _client_ip()
        attempts = _prune_attempts(ip, current_app.config['ADMIN_LOGIN_WINDOW_SECONDS'])
        if len(attempts) >= current_app.config['ADMIN_LOGIN_MAX_ATTEMPTS']:
            flash('Too many login attempts. Please wait and try again.', 'danger')
            return render_template('admin/login.html'), 429

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        admin = db.session.query(AdminUser).filter_by(email=email).first()

        if admin and bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            login_user(admin, remember=True)
            _LOGIN_ATTEMPTS.pop(ip, None)
            next_page = _safe_next_url(request.args.get('next'))
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('crm_dashboard.dashboard'))
        else:
            attempts.append(time())
            flash('Invalid email or password.', 'danger')

    return render_template('admin/login.html')


@crm_auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('crm_auth.login'))
