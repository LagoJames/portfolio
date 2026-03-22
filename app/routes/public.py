from flask import Blueprint, render_template, request, abort, current_app
from app import db
from app.models import (Project, Testimonial, Skill, Notebook, Setting,
                        ActiveProject, ClientReview, HireRequest, HireRequestFile,
                        ReviewToken)
from app.utils.helpers import slugify, render_markdown
from datetime import datetime, timezone
import os
import uuid
from werkzeug.utils import secure_filename

public = Blueprint('public', __name__)


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
    categories = db.session.query(Project.category).filter_by(is_visible=True)\
        .distinct().all()
    categories = [c[0] for c in categories]
    return render_template('public/work.html', projects=projects, categories=categories)


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
                           testimonials=testimonials)


@public.route('/contact')
def contact():
    return render_template('public/contact.html')


@public.route('/hire', methods=['GET', 'POST'])
def hire():
    if request.method == 'POST':
        # Process hiring form
        hr = HireRequest(
            client_name=request.form.get('client_name', '').strip(),
            client_email=request.form.get('client_email', '').strip(),
            client_phone=request.form.get('client_phone', '').strip(),
            is_anonymous=request.form.get('is_anonymous') == 'on',
            project_title=request.form.get('project_title', '').strip(),
            project_description=request.form.get('project_description', '').strip(),
            ai_summary=request.form.get('ai_summary', '').strip(),
            deliverables=request.form.get('deliverables', '').strip(),
            payment_method=request.form.get('payment_method', ''),
            pricing_type=request.form.get('pricing_type', ''),
            payment_schedule=request.form.get('payment_schedule', ''),
            total_amount=float(request.form.get('total_amount', 0) or 0),
            deposit_amount=float(request.form.get('deposit_amount', 0) or 0),
        )

        # Parse deadline
        deadline_str = request.form.get('deadline', '')
        if deadline_str:
            try:
                from datetime import datetime
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
                os.makedirs(upload_dir, exist_ok=True)
                original = secure_filename(f.filename)
                unique_name = f"{uuid.uuid4().hex}_{original}"
                f.save(os.path.join(upload_dir, unique_name))
                hrf = HireRequestFile(
                    hire_request_id=hr.id,
                    filename=unique_name,
                    original_filename=original,
                    file_size=f.content_length or 0
                )
                db.session.add(hrf)

        db.session.commit()

        # Send notification
        try:
            from app.utils.notify import notify_hire_request
            notify_hire_request(hr)
        except Exception:
            pass  # Don't fail the request if notification fails

        return render_template('public/hire_success.html')

    return render_template('public/hire.html')


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
    availability = Setting.query.filter_by(key='availability_status').first()
    return render_template('public/status.html',
                           active_project=active,
                           availability=availability)


@public.route('/samples')
def samples():
    """Work samples page — notebooks and papers for potential clients."""
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
    papers = [
        {'file': 'comparing-arch-garch-models.docx', 'title': 'Comparing ARCH and GARCH Models', 'category': 'Econometrics', 'desc': 'Comparative analysis of ARCH and GARCH volatility modelling approaches.'},
        {'file': 'interrelations-global-capital-markets.docx', 'title': 'Interrelations Among Global Capital Markets', 'category': 'Financial Economics', 'desc': 'Investigation of co-movement and interdependence across major world capital markets.'},
        {'file': 'capital-transition-bank-systemic-risk.docx', 'title': 'Capital Transition & Bank Systemic Risk', 'category': 'Banking & Risk', 'desc': 'Analysis of capital transitional arrangements and their effect on bank systemic risk.'},
        {'file': 'determinants-economic-growth.docx', 'title': 'Determinants of Economic Growth', 'category': 'Macroeconomics', 'desc': 'Econometric study of factors driving economic growth.'},
        {'file': 'statistical-analysis-business.docx', 'title': 'Statistical Analysis for Business', 'category': 'Statistics', 'desc': 'Applied statistical methods for business decision-making.'},
    ]
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
