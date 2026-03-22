#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

flask db upgrade

# Only seed if database is empty
python -c "
from app import create_app, db
from app.models import Project
app = create_app()
with app.app_context():
    if Project.query.count() == 0:
        print('Database empty, running seed...')
        exec(open('seed.py').read())
    else:
        print('Database already seeded, skipping.')
"
