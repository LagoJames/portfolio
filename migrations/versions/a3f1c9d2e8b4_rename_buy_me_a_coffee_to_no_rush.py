"""Rename buy_me_a_coffee to no_rush on hire_requests

Revision ID: a3f1c9d2e8b4
Revises: b1d4f2a98c7e
Create Date: 2026-03-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f1c9d2e8b4'
down_revision = 'd2c8a7f4c1be'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('no_rush', sa.Boolean(), nullable=True))

    op.execute("UPDATE hire_requests SET no_rush = FALSE")

    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('buy_me_a_coffee')


def downgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('buy_me_a_coffee', sa.Boolean(), nullable=True))

    op.execute("UPDATE hire_requests SET buy_me_a_coffee = FALSE")

    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('no_rush')
