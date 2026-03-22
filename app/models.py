from datetime import datetime, timezone
from flask_login import UserMixin
from app import db


class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── PORTFOLIO PROJECTS ──────────────────────────────────────────────
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False)

    category = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(30), default='upwork')

    short_description = db.Column(db.Text)
    full_description = db.Column(db.Text)
    tools_used = db.Column(db.String(1000))
    cover_image_url = db.Column(db.String(500))

    github_url = db.Column(db.String(500))
    colab_url = db.Column(db.String(500))
    substack_url = db.Column(db.String(500))
    paper_url = db.Column(db.String(500))
    upwork_url = db.Column(db.String(500))

    upwork_rating = db.Column(db.Float)

    is_featured = db.Column(db.Boolean, default=False)
    is_visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    testimonials = db.relationship('Testimonial', backref='project', lazy=True)
    client_reviews = db.relationship('ClientReview', backref='project', lazy=True)


# ── TESTIMONIALS ────────────────────────────────────────────────────
class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255))
    job_title = db.Column(db.String(500))
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float)
    source = db.Column(db.String(30), default='upwork')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    is_visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── CLIENT REVIEWS (public reviews on portfolio projects) ───────────
class ClientReview(db.Model):
    __tablename__ = 'client_reviews'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    reviewer_name = db.Column(db.String(255), nullable=False)
    reviewer_email = db.Column(db.String(255))
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    review_text = db.Column(db.Text, nullable=False)
    review_token = db.Column(db.String(100))  # token sent to client to authenticate review
    is_approved = db.Column(db.Boolean, default=False)
    is_visible = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── BLOG POSTS ──────────────────────────────────────────────────────
class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    cover_image_url = db.Column(db.String(500))
    category = db.Column(db.String(50), default='thoughts')
    # Values: thoughts, books, music, movies, technology, markets, life
    tags = db.Column(db.String(500))  # comma-separated
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))


# ── REVIEW TOKENS (for project owner authentication) ────────────────
class ReviewToken(db.Model):
    __tablename__ = 'review_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)

    project = db.relationship('Project', backref='review_tokens')


# ── COLAB NOTEBOOKS ─────────────────────────────────────────────────
class Notebook(db.Model):
    __tablename__ = 'notebooks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    tools_used = db.Column(db.String(500))
    colab_url = db.Column(db.String(500), nullable=False)
    cover_image_url = db.Column(db.String(500))
    category = db.Column(db.String(50))
    source = db.Column(db.String(30), default='personal')
    is_visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── SKILLS ──────────────────────────────────────────────────────────
class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


# ── CONTACT SUBMISSIONS ────────────────────────────────────────────
class ContactSubmission(db.Model):
    __tablename__ = 'contact_submissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    message = db.Column(db.Text, nullable=False)
    project_type = db.Column(db.String(100))
    budget_range = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── HIRE REQUESTS (client hiring form) ──────────────────────────────
class HireRequest(db.Model):
    __tablename__ = 'hire_requests'
    id = db.Column(db.Integer, primary_key=True)

    # Client info
    client_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)
    client_phone = db.Column(db.String(50))
    is_anonymous = db.Column(db.Boolean, default=False)

    # Project details
    project_title = db.Column(db.String(500), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    ai_summary = db.Column(db.Text)
    deliverables = db.Column(db.Text)
    deadline = db.Column(db.DateTime)

    # Payment details
    payment_method = db.Column(db.String(50))  # card, mpesa, stripe, wise
    pricing_type = db.Column(db.String(30))  # hourly, fixed
    payment_schedule = db.Column(db.String(30))  # once, installments, deposit, end_of_job
    total_amount = db.Column(db.Float)
    deposit_amount = db.Column(db.Float)

    # Status
    status = db.Column(db.String(30), default='pending')
    # Values: pending, reviewing, accepted, in_progress, completed, declined
    admin_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to files
    files = db.relationship('HireRequestFile', backref='hire_request', lazy=True)


class HireRequestFile(db.Model):
    __tablename__ = 'hire_request_files'
    id = db.Column(db.Integer, primary_key=True)
    hire_request_id = db.Column(db.Integer, db.ForeignKey('hire_requests.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── ACTIVE PROJECTS (what James is currently working on) ────────────
class ActiveProject(db.Model):
    __tablename__ = 'active_projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(500), nullable=False)
    client_name = db.Column(db.String(255))
    is_private = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    expected_finish = db.Column(db.DateTime)
    status = db.Column(db.String(30), default='in_progress')
    # Values: in_progress, completed, paused, cancelled
    source = db.Column(db.String(30), default='website')  # website, external
    hire_request_id = db.Column(db.Integer, db.ForeignKey('hire_requests.id'), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    hire_request = db.relationship('HireRequest', backref='active_project', uselist=False)


# ── PROJECT MANAGEMENT (from spreadsheet) ───────────────────────────
class PMClient(db.Model):
    __tablename__ = 'pm_clients'
    id = db.Column(db.Integer, primary_key=True)
    client_id_code = db.Column(db.String(20))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    pm_projects = db.relationship('PMProject', backref='client', lazy=True)


class PMProject(db.Model):
    __tablename__ = 'pm_projects'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('pm_clients.id'), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(30), default='ongoing')
    # Values: ongoing, completed, paused, cancelled
    budget = db.Column(db.Float)
    amount_paid = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    tasks = db.relationship('PMTask', backref='project', lazy=True)
    payments = db.relationship('PMPayment', backref='project', lazy=True)
    invoices = db.relationship('PMInvoice', backref='project', lazy=True)


class PMTask(db.Model):
    __tablename__ = 'pm_tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_id_code = db.Column(db.String(20))
    project_id = db.Column(db.Integer, db.ForeignKey('pm_projects.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    status = db.Column(db.String(30), default='not_started')
    # Values: not_started, in_progress, completed, blocked
    due_date = db.Column(db.DateTime)
    priority = db.Column(db.String(10), default='3/5')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    logs = db.relationship('PMTaskLog', backref='task', lazy=True)


class PMTaskLog(db.Model):
    __tablename__ = 'pm_task_logs'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('pm_tasks.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    actual_time = db.Column(db.String(50))
    status = db.Column(db.String(30))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PMPayment(db.Model):
    __tablename__ = 'pm_payments'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('pm_projects.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    invoice_id = db.Column(db.Integer, db.ForeignKey('pm_invoices.id'), nullable=True)
    receipt_id = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PMInvoice(db.Model):
    __tablename__ = 'pm_invoices'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('pm_projects.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True)
    date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('pm_tasks.id'), nullable=True)
    payment_status = db.Column(db.String(30), default='unpaid')
    payment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PMExpense(db.Model):
    __tablename__ = 'pm_expenses'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    item = db.Column(db.String(500), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── SETTINGS (key-value store) ──────────────────────────────────────
class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
