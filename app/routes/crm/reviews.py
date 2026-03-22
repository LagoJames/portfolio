from flask import Blueprint, redirect, url_for, flash, request, render_template_string
from flask_login import login_required
from flask import render_template
from app import db
from app.models import ClientReview, ReviewToken, Project
from datetime import datetime, timezone, timedelta
import uuid

crm_reviews = Blueprint('crm_reviews', __name__, url_prefix='/admin/crm/reviews')


@crm_reviews.route('/')
@login_required
def list_reviews():
    # Pending reviews (not yet approved) appear first, then approved, sorted by date within each group.
    reviews = (
        ClientReview.query
        .order_by(ClientReview.is_approved.asc(), ClientReview.created_at.desc())
        .all()
    )
    return render_template('admin/reviews_list.html', reviews=reviews)


@crm_reviews.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve_review(id):
    review = ClientReview.query.get_or_404(id)
    review.is_approved = True
    review.is_visible  = True
    db.session.commit()
    flash(f'Review by "{review.reviewer_name}" approved and set to visible.', 'success')
    return redirect(url_for('crm_reviews.list_reviews'))


@crm_reviews.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_review(id):
    review = ClientReview.query.get_or_404(id)
    review.is_approved = False
    review.is_visible  = False
    db.session.commit()
    flash(f'Review by "{review.reviewer_name}" rejected and hidden.', 'success')
    return redirect(url_for('crm_reviews.list_reviews'))


@crm_reviews.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_review(id):
    review = ClientReview.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted.', 'success')
    return redirect(url_for('crm_reviews.list_reviews'))


# ── GENERATE REVIEW TOKEN ────────────────────────────────────────────
@crm_reviews.route('/generate-token', methods=['GET', 'POST'])
@login_required
def generate_review_token():
    projects = Project.query.filter_by(is_visible=True).order_by(Project.title).all()
    review_url = None
    token_value = None

    if request.method == 'POST':
        project_id = request.form.get('project_id', '').strip()
        client_email = request.form.get('client_email', '').strip()

        if not project_id or not client_email:
            flash('Project and client email are required.', 'danger')
        else:
            project = Project.query.get_or_404(int(project_id))
            token_value = uuid.uuid4().hex
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            review_token = ReviewToken(
                token=token_value,
                project_id=project.id,
                client_email=client_email,
                is_used=False,
                expires_at=expires_at,
            )
            db.session.add(review_token)
            db.session.commit()

            review_url = url_for(
                'public.project_detail',
                slug=project.slug,
                token=token_value,
                _external=True,
            )
            flash(f'Review token generated for {client_email}.', 'success')

    return render_template(
        'admin/generate_review_token.html',
        projects=projects,
        review_url=review_url,
        token_value=token_value,
    )
