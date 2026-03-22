from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Skill

crm_skills = Blueprint('crm_skills', __name__, template_folder='../../../templates')

VALID_CATEGORIES = ('languages', 'ml_frameworks', 'quant_finance', 'statistics', 'tools')


@crm_skills.route('/')
@login_required
def list_skills():
    skills = (
        db.session.query(Skill)
        .order_by(Skill.category.asc(), Skill.sort_order.asc(), Skill.name.asc())
        .all()
    )
    return render_template('admin/skills_list.html', skills=skills, categories=VALID_CATEGORIES)


@crm_skills.route('/new', methods=['GET', 'POST'])
@login_required
def new_skill():
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        if category not in VALID_CATEGORIES:
            flash(f'Invalid category. Choose one of: {", ".join(VALID_CATEGORIES)}.', 'danger')
            return render_template('admin/skill_form.html', skill=None, categories=VALID_CATEGORIES)

        skill = Skill(
            name=request.form.get('name', '').strip(),
            category=category,
            sort_order=int(request.form.get('sort_order') or 0),
            is_visible=bool(request.form.get('is_visible')),
        )
        db.session.add(skill)
        db.session.commit()
        flash('Skill created successfully.', 'success')
        return redirect(url_for('crm_skills.list_skills'))

    return render_template('admin/skill_form.html', skill=None, categories=VALID_CATEGORIES)


@crm_skills.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_skill(id):
    skill = db.session.get(Skill, id)
    if skill is None:
        flash('Skill not found.', 'danger')
        return redirect(url_for('crm_skills.list_skills'))

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        if category not in VALID_CATEGORIES:
            flash(f'Invalid category. Choose one of: {", ".join(VALID_CATEGORIES)}.', 'danger')
            return render_template('admin/skill_form.html', skill=skill, categories=VALID_CATEGORIES)

        skill.name = request.form.get('name', '').strip()
        skill.category = category
        skill.sort_order = int(request.form.get('sort_order') or 0)
        skill.is_visible = bool(request.form.get('is_visible'))
        db.session.commit()
        flash('Skill updated successfully.', 'success')
        return redirect(url_for('crm_skills.list_skills'))

    return render_template('admin/skill_form.html', skill=skill, categories=VALID_CATEGORIES)


@crm_skills.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_skill(id):
    skill = db.session.get(Skill, id)
    if skill is None:
        flash('Skill not found.', 'danger')
        return redirect(url_for('crm_skills.list_skills'))

    db.session.delete(skill)
    db.session.commit()
    flash('Skill deleted.', 'success')
    return redirect(url_for('crm_skills.list_skills'))
