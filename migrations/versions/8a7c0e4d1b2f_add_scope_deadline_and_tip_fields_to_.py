"""Add scope, deadline, and tip fields to hire_requests

Revision ID: 8a7c0e4d1b2f
Revises: 58e9ee6c1fe2
Create Date: 2026-03-27 18:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a7c0e4d1b2f'
down_revision = '58e9ee6c1fe2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deadline_time', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('deadline_flexibility', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('scope_change_budget', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('tip_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('buy_me_a_coffee', sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('buy_me_a_coffee')
        batch_op.drop_column('tip_amount')
        batch_op.drop_column('scope_change_budget')
        batch_op.drop_column('deadline_flexibility')
        batch_op.drop_column('deadline_time')
