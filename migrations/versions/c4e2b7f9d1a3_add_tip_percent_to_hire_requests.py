"""Add tip_percent to hire_requests

Revision ID: c4e2b7f9d1a3
Revises: a3f1c9d2e8b4
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4e2b7f9d1a3'
down_revision = 'a3f1c9d2e8b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tip_percent', sa.String(10), nullable=True))


def downgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('tip_percent')
