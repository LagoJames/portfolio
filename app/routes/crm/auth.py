import bcrypt
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import AdminUser

crm_auth = Blueprint('crm_auth', __name__, template_folder='../../../templates')


@crm_auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('crm_dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        admin = db.session.query(AdminUser).filter_by(email=email).first()

        if admin and bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            login_user(admin, remember=True)
            next_page = request.args.get('next')
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('crm_dashboard.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('admin/login.html')


@crm_auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('crm_auth.login'))
