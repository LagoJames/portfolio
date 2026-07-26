"""add contract fields to hire requests

Revision ID: b1d4f2a98c7e
Revises: 8a7c0e4d1b2f
Create Date: 2026-03-27 19:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1d4f2a98c7e'
down_revision = '8a7c0e4d1b2f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contract_signed', sa.Boolean(), nullable=True))

    with op.batch_alter_table('hire_request_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_kind', sa.String(length=50), nullable=True))

    op.execute("UPDATE hire_requests SET contract_signed = FALSE WHERE contract_signed IS NULL")
    op.execute("UPDATE hire_request_files SET file_kind = 'supporting' WHERE file_kind IS NULL")


def downgrade():
    with op.batch_alter_table('hire_request_files', schema=None) as batch_op:
        batch_op.drop_column('file_kind')

    with op.batch_alter_table('hire_requests', schema=None) as batch_op:
        batch_op.drop_column('contract_signed')
