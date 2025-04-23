"""Create users table

Revision ID: 001
Revises: 
Create Date: 2023-06-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('telegram_id', sa.Integer, nullable=False, unique=True, index=True),
        sa.Column('username', sa.String, nullable=True),
        sa.Column('first_name', sa.String, nullable=True),
        sa.Column('last_name', sa.String, nullable=True),
        sa.Column('first_contact', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_contact', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade():
    op.drop_table('users')
