"""add stripe fields to hire requests

Revision ID: d2c8a7f4c1be
Revises: b1d4f2a98c7e
Create Date: 2026-03-27 19:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2c8a7f4c1be'
down_revision = 'b1d4f2a98c7e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_checkout_session_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('stripe_payment_intent_id')
        batch_op.drop_column('stripe_checkout_session_id')
