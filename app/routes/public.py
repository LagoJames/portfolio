from flask import Blueprint, render_template, request, abort, current_app, redirect, url_for, send_from_directory
from app import db
from app.models import (Project, Testimonial, Skill, Notebook, Setting,
                        ActiveProject, ClientReview, HireRequest, HireRequestFile,
                        ReviewToken)
from app.utils.helpers import slugify, render_markdown
from app.utils.art_catalog import ART_FACEBOOK_URL, gallery_items, store_prints
from app.utils.stripe_checkout import create_checkout_session
from datetime import datetime, timezone
import os
import uuid
from werkzeug.utils import secure_filename

public = Blueprint('public', __name__)

ALLOWED_HIRE_UPLOAD_EXTENSIONS = {
    'signed_contract': {'pdf'},
    'signed_nda': {'pdf'},
    'supporting': {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'},
}
ALLOWED_HIRE_UPLOAD_MIME_PREFIXES = {
    'signed_contract': ('application/pdf',),
    'signed_nda': ('application/pdf',),
    'supporting': (
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'image/png',
        'image/jpeg',
    ),
}


def _category_label(category):
    labels = {
        'financial_engineering': 'Quantitative Finance',
        'machine_learning': 'Machine Learning',
        'trading_quant': 'Quantitative Trading',
        'statistical_analysis': 'Statistical Analyses',
        'research': 'Research',
        'personal': 'Personal Projects',
        'web_development': 'Web Development',
        'pinescript': 'Pine Script',
        'ghostwriting': 'Academic Writing',
    }
    return labels.get(category, category.replace('_', ' ').title())


def _save_hire_file(file_storage, upload_dir, hire_request_id, kind):
    if not file_storage or not file_storage.filename:
        return None

    os.makedirs(upload_dir, exist_ok=True)
    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    allowed_exts = ALLOWED_HIRE_UPLOAD_EXTENSIONS.get(kind, set())
    if ext not in allowed_exts:
        raise ValueError(f'Unsupported file type for {kind.replace("_", " ")}. Allowed: {", ".join(sorted(allowed_exts))}.')

    content_type = (file_storage.mimetype or '').lower()
    allowed_mimes = ALLOWED_HIRE_UPLOAD_MIME_PREFIXES.get(kind, ())
    if content_type and content_type not in allowed_mimes:
        raise ValueError(f'Unsupported upload content type for {kind.replace("_", " ")}.')

    MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
    file_storage.stream.seek(0, 2)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if file_size > MAX_FILE_BYTES:
        raise ValueError(f'File "{original}" exceeds the 10 MB limit ({file_size // (1024*1024)} MB). Please compress or split the file.')

    unique_name = f"{kind}_{uuid.uuid4().hex}_{original}"
    file_storage.save(os.path.join(upload_dir, unique_name))
    saved = HireRequestFile(
        hire_request_id=hire_request_id,
        filename=unique_name,
        original_filename=original,
        file_kind=kind,
        file_size=file_storage.content_length or 0
    )
    db.session.add(saved)
    return saved


@public.route('/')
def home():
    featured = Project.query.filter_by(is_featured=True, is_visible=True)\
        .order_by(Project.sort_order).limit(3).all()
    testimonials = Testimonial.query.filter_by(is_visible=True)\
        .order_by(Testimonial.sort_order).all()
    skills = Skill.query.filter_by(is_visible=True)\
        .order_by(Skill.category, Skill.sort_order).all()

    # Group skills by category
    skill_groups = {}
    for s in skills:
        skill_groups.setdefault(s.category, []).append(s)

    # Try to get live Substack posts
    recent_posts = []
    try:
        from app.utils.substack import get_quant_hedge_posts
        recent_posts = get_quant_hedge_posts(3)
    except Exception:
        pass

    # Current active project for status display
    active = ActiveProject.query.filter_by(
        status='in_progress', is_private=False, is_anonymous=False
    ).first()

    return render_template('public/home.html',
                           featured=featured,
                           testimonials=testimonials,
                           skill_groups=skill_groups,
                           recent_posts=recent_posts,
                           active_project=active)


@public.route('/work')
def work():
    projects = Project.query.filter_by(is_visible=True)\
        .order_by(Project.sort_order, Project.created_at.desc()).all()
    category_rows = db.session.query(Project.category).filter_by(is_visible=True).distinct().all()
    categories = []
    for row in category_rows:
        key = row[0]
        categories.append({
            'key': key,
            'label': _category_label(key),
            'count': len([project for project in projects if project.category == key]),
        })
    return render_template('public/work.html', projects=projects, categories=categories, category_label=_category_label)


@public.route('/work/<slug>')
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, is_visible=True).first_or_404()
    related = Project.query.filter_by(category=project.category, is_visible=True)\
        .filter(Project.id != project.id).limit(3).all()
    testimonial = Testimonial.query.filter_by(project_id=project.id, is_visible=True).first()

    # Approved client reviews
    reviews = ClientReview.query.filter_by(
        project_id=project.id, is_approved=True, is_visible=True
    ).order_by(ClientReview.created_at.desc()).all()

    # Validate review token from query string
    review_token_valid = False
    token_value = request.args.get('token', '').strip()
    if token_value:
        now = datetime.now(timezone.utc)
        rt = ReviewToken.query.filter_by(
            token=token_value,
            project_id=project.id,
            is_used=False,
        ).first()
        if rt and (rt.expires_at is None or rt.expires_at.replace(tzinfo=timezone.utc) > now):
            review_token_valid = True

    description_html = render_markdown(project.full_description)
    return render_template('public/project_detail.html',
                           project=project,
                           related=related,
                           testimonial=testimonial,
                           reviews=reviews,
                           description_html=description_html,
                           review_token_valid=review_token_valid)


@public.route('/writing')
def writing():
    notebooks = Notebook.query.filter_by(is_visible=True)\
        .order_by(Notebook.sort_order).all()

    quant_posts = []
    jarida_posts = []
    repos = []
    try:
        from app.utils.substack import get_quant_hedge_posts, get_jarida_posts
        quant_posts = get_quant_hedge_posts(20)
        jarida_posts = get_jarida_posts(6)
    except Exception:
        pass
    try:
        from app.utils.github import get_repos
        repos = get_repos(6)
    except Exception:
        pass

    return render_template('public/writing.html',
                           notebooks=notebooks,
                           quant_posts=quant_posts,
                           jarida_posts=jarida_posts,
                           repos=repos)


@public.route('/about')
def about():
    skills = Skill.query.filter_by(is_visible=True)\
        .order_by(Skill.category, Skill.sort_order).all()
    skill_groups = {}
    for s in skills:
        skill_groups.setdefault(s.category, []).append(s)

    testimonials = Testimonial.query.filter_by(is_visible=True)\
        .order_by(Testimonial.sort_order).limit(6).all()

    return render_template('public/about.html',
                           skill_groups=skill_groups,
                           testimonials=testimonials,
                           art_gallery=gallery_items(),
                           art_facebook_url=ART_FACEBOOK_URL)


@public.route('/contact')
def contact():
    return render_template('public/contact.html')


@public.route('/store')
def store():
    products = [
        {
            'title': 'VIX Replication in R',
            'subtitle': 'Quantitative Finance Toolkit',
            'description': 'An R-based VIX replication product for volatility research, study, and implementation work.',
            'price_label': 'Available on Gumroad',
            'url': 'https://lagobrian.gumroad.com/l/vix-replication-r',
            'checkout_kind': 'external',
        }
    ] + store_prints()
    return render_template(
        'public/store.html',
        products=products,
    )


@public.route('/store/download/<slug>')
def store_download(slug):
    product = next((item for item in store_prints() if item['slug'] == slug), None)
    if not product:
        abort(404)
    relative_path = product['download_filename']
    directory, filename = relative_path.rsplit('/', 1)
    return send_from_directory(
        os.path.join(current_app.static_folder, directory),
        filename,
        as_attachment=True,
        download_name=filename,
    )


@public.route('/privacy')
def privacy():
    return render_template('public/privacy.html')


@public.route('/cookies')
def cookies():
    return render_template('public/cookies.html')


@public.route('/hire', methods=['GET', 'POST'])
def hire():
    if request.method == 'POST':
        try:
            signed_contract = request.files.get('signed_contract')
            if not signed_contract or not signed_contract.filename:
                from flask import flash
                flash('Please sign and upload the client services agreement before submitting your hire request.', 'error')
                return render_template('public/hire.html', now=datetime.now(timezone.utc))

            payment_method = request.form.get('payment_method', '')
            manual_methods = ('wise', 'mpesa')
            if payment_method in manual_methods:
                payment_status = 'awaiting_confirmation'
            elif payment_method == 'stripe':
                payment_status = 'pending_checkout'
            else:
                payment_status = 'not_required'

            hr = HireRequest(
                client_name=request.form.get('client_name', '').strip(),
                client_email=request.form.get('client_email', '').strip(),
                client_phone=request.form.get('client_phone', '').strip(),
                whatsapp_number=request.form.get('whatsapp_number', '').strip() or None,
                is_anonymous=request.form.get('is_anonymous') == 'on',
                project_title=request.form.get('project_title', '').strip(),
                project_description=request.form.get('project_description', '').strip(),
                ai_summary=request.form.get('ai_summary', '').strip(),
                deliverables=request.form.get('deliverables', '').strip(),
                payment_method=payment_method,
                payment_status=payment_status,
                pricing_type=request.form.get('pricing_type', ''),
                payment_schedule=request.form.get('payment_schedule', ''),
                total_amount=float(request.form.get('total_amount', 0) or 0),
                deposit_amount=float(request.form.get('deposit_amount', 0) or 0),
                deadline_time=request.form.get('deadline_time', '').strip() or None,
                deadline_flexibility=request.form.get('deadline_flexibility', 'soft').strip() or 'soft',
                scope_change_budget=request.form.get('scope_change_budget', 'fixed').strip() or 'fixed',
                tip_amount=float(request.form.get('tip_amount', 0) or 0),
                tip_percent=request.form.get('tip_percent', '0') or '0',
                no_rush=request.form.get('no_rush') == 'on',
                mpesa_confirmation=request.form.get('mpesa_confirmation', '').strip() or None,
                nda_signed=request.form.get('nda_signed') == 'on',
                contract_signed=True,
                invoice_email=request.form.get('invoice_email', '').strip() or None,
                invoice_opt_out=request.form.get('invoice_opt_out') == 'on',
            )

            deadline_str = request.form.get('deadline', '')
            if deadline_str:
                try:
                    hr.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                except ValueError:
                    pass

            db.session.add(hr)
            db.session.flush()

            # Handle file uploads
            files = request.files.getlist('files')
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'client_files', str(hr.id))
            for f in files:
                if f and f.filename:
                    _save_hire_file(f, upload_dir, hr.id, 'supporting')

            if signed_contract and signed_contract.filename:
                _save_hire_file(signed_contract, upload_dir, hr.id, 'signed_contract')

            signed_nda = request.files.get('signed_nda')
            if signed_nda and signed_nda.filename:
                _save_hire_file(signed_nda, upload_dir, hr.id, 'signed_nda')

            db.session.commit()

            # Send notification in background thread (never blocks)
            try:
                from app.utils.notify import notify_hire_request
                notify_hire_request(hr)
            except Exception:
                current_app.logger.exception('notify_hire_request failed for hire_request id=%s', hr.id)

            # WhatsApp instant alert to yourself
            try:
                from app.utils.whatsapp import alert_hire
                budget_str = f'${hr.total_amount:.0f}' if hr.total_amount else 'TBD'
                alert_hire(
                    name=hr.client_name or 'Anonymous',
                    email=hr.client_email,
                    project_title=hr.project_title,
                    budget=budget_str,
                    payment_method=payment_method,
                )
            except Exception:
                current_app.logger.exception('alert_hire WhatsApp failed for hire_request id=%s', hr.id)

            # WhatsApp confirmation to client (TextMeBot — from your number)
            try:
                from app.utils.whatsapp import confirm_hire_client
                confirm_hire_client(
                    name=hr.client_name or '',
                    phone=hr.whatsapp_number or hr.client_phone or '',
                    project_title=hr.project_title,
                )
            except Exception:
                current_app.logger.exception('confirm_hire_client WhatsApp failed for hire_request id=%s', hr.id)

            if payment_method == 'stripe':
                try:
                    session = create_checkout_session(hr)
                    hr.stripe_checkout_session_id = session.id
                    db.session.commit()
                    return redirect(session.url, code=303)
                except Exception as e:
                    current_app.logger.exception('Stripe checkout session creation failed')
                    hr.payment_status = 'pending_checkout'
                    db.session.commit()
                    from flask import flash
                    flash('Your brief was received, but Stripe checkout could not start right now. I will follow up by email to complete payment.', 'warning')
                    return render_template('public/hire_pending.html', hr=hr)

            if payment_method in manual_methods:
                return render_template('public/hire_pending.html', hr=hr)
            return render_template('public/hire_success.html')

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Hire form failed: {e}")
            from flask import flash
            flash(str(e) if isinstance(e, ValueError) else 'Something went wrong. Please try again or email lagobrian@outlook.com directly.', 'error')
            return render_template('public/hire.html', now=datetime.now(timezone.utc))

    return render_template('public/hire.html', now=datetime.now(timezone.utc))


@public.route('/hire/success')
def hire_success_page():
    session_id = request.args.get('session_id', '').strip()
    hr = HireRequest.query.filter_by(stripe_checkout_session_id=session_id).first() if session_id else None
    payment_complete = bool(hr and hr.payment_status == 'confirmed')
    return render_template('public/hire_success.html', hr=hr, payment_complete=payment_complete)


@public.route('/nda.pdf')
def download_nda():
    """Download the blank NDA PDF."""
    import tempfile, os
    from flask import send_file
    from app.utils.nda_pdf import generate_nda
    tmp = tempfile.mktemp(suffix='.pdf')
    generate_nda(tmp)
    return send_file(tmp, as_attachment=True, download_name='Lago_Brian_NDA.pdf', mimetype='application/pdf')


@public.route('/services-agreement.pdf')
def download_services_agreement():
    """Download the standard client services agreement PDF."""
    import tempfile
    from flask import send_file
    from app.utils.service_contract_pdf import generate_services_agreement
    tmp = tempfile.mktemp(suffix='.pdf')
    generate_services_agreement(tmp)
    return send_file(tmp, as_attachment=True, download_name='Lago_Brian_Client_Services_Agreement.pdf', mimetype='application/pdf')


@public.route('/work/<slug>/review', methods=['POST'])
def submit_review(slug):
    project = Project.query.filter_by(slug=slug, is_visible=True).first_or_404()

    # Validate the review token passed in query string
    token_value = request.args.get('token', '').strip()
    if not token_value:
        abort(403)

    now = datetime.now(timezone.utc)
    rt = ReviewToken.query.filter_by(
        token=token_value,
        project_id=project.id,
        is_used=False,
    ).first()
    if not rt or (rt.expires_at is not None and rt.expires_at.replace(tzinfo=timezone.utc) <= now):
        abort(403)

    review = ClientReview(
        project_id=project.id,
        reviewer_name=request.form.get('reviewer_name', '').strip(),
        reviewer_email=request.form.get('reviewer_email', '').strip(),
        rating=int(request.form.get('rating', 5)),
        review_text=request.form.get('review_text', '').strip(),
        is_approved=False,
        is_visible=False,
    )
    db.session.add(review)

    # Mark token as used
    rt.is_used = True
    db.session.commit()

    return render_template('public/review_submitted.html', project=project)


@public.route('/status')
def status():
    """Public endpoint showing if James is currently engaged."""
    active = ActiveProject.query.filter_by(
        status='in_progress', is_private=False, is_anonymous=False
    ).first()
    return render_template('public/status.html', active_project=active)


@public.route('/samples')
def samples():
    """Work samples page — notebooks and papers for potential clients."""
    import json as _json
    notebooks = [
        {'file': 'differential-deep-learning-pytorch.ipynb', 'title': 'Differential Deep Learning (TF to PyTorch)', 'category': 'Derivatives Pricing',
         'desc': 'Converted Antoine Savine\'s Differential Deep Learning from TensorFlow to PyTorch, achieving 2+ second speed gains. Twin networks with differential training for options pricing and Greeks computation.',
         'tools': ['PyTorch', 'Black-Scholes', 'Greeks', 'Neural Networks']},
        {'file': 'deep-learning-0dte-options-trading.ipynb', 'title': 'Deep Learning for 0DTE Options Trading', 'category': 'Trading & ML',
         'desc': 'PyTorch deep learning model for zero-days-to-expiration Nifty options. Feature engineering from 211 days of 1-minute data, strike identification, entry/exit labelling, and technical indicator selection.',
         'tools': ['PyTorch', 'Options', 'Feature Engineering', 'Nifty']},
        {'file': 'bayesian-instrumental-variables-gibbs-sampling.ipynb', 'title': 'Bayesian IV Models via Gibbs Sampling', 'category': 'Econometrics',
         'desc': 'Bayesian analysis of instrumental variable models using Gibbs sampling. Full posterior estimation of education effects on income with MCMC diagnostics and 3D distribution visualisations.',
         'tools': ['Python', 'Bayesian', 'Gibbs Sampling', 'IV Models']},
        {'file': 'topological-data-analysis-epileptic-seizure-detection.ipynb', 'title': 'TDA for Epileptic Seizure Detection', 'category': 'Machine Learning',
         'desc': 'Topological Data Analysis augmenting ML/DL for epileptic seizure classification. Persistent homology features combined with GRU, LSTM, and classical ML models. SMOTE for class balancing.',
         'tools': ['Python', 'TDA', 'GRU', 'LSTM', 'Persistent Homology']},
        {'file': 'supervised-fault-detection-gru.ipynb', 'title': 'Supervised Fault Detection (GRU)', 'category': 'Deep Learning',
         'desc': 'GRU-based supervised fault detection and classification across 5 fault types in sensor data. Ray Tune hyperparameter optimisation, custom PyTorch DataLoaders, and TensorBoard logging.',
         'tools': ['PyTorch', 'GRU', 'Ray Tune', 'Classification']},
        {'file': 'unsupervised-fault-detection-gru.ipynb', 'title': 'Unsupervised Fault Detection (GRU)', 'category': 'Deep Learning',
         'desc': 'Unsupervised anomaly detection in industrial sensor data using GRU autoencoders. Reconstruction error-based fault detection with TensorFlow and PyTorch implementations.',
         'tools': ['PyTorch', 'TensorFlow', 'GRU', 'Autoencoders']},
    ]
    # Load papers from metadata file (managed via admin)
    metadata_path = os.path.join(current_app.root_path, 'static', 'samples', 'papers', 'metadata.json')
    try:
        with open(metadata_path) as f:
            papers = _json.load(f)
    except Exception:
        papers = []
    return render_template('public/samples.html', notebooks=notebooks, papers=papers)


@public.route('/sitemap.xml')
def sitemap():
    projects = Project.query.filter_by(is_visible=True).all()
    return render_template('sitemap.xml', projects=projects), 200, {
        'Content-Type': 'application/xml'
    }


@public.route('/robots.txt')
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://lagobrian.com/sitemap.xml", 200, {
        'Content-Type': 'text/plain'
    }
