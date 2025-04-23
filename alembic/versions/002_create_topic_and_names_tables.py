"""Create topic and names tables

Revision ID: 002
Revises: 001
Create Date: 2023-11-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create topic table
    op.create_table(
        'topic',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String, nullable=False, unique=True, index=True)
    )
    
    # Create names table
    op.create_table(
        'names',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('first_name', sa.String, nullable=False),
        sa.Column('last_name', sa.String, nullable=False)
    )


def downgrade():
    op.drop_table('names')
    op.drop_table('topic')
