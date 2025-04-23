"""Create jobs, cities, activities, and persons tables

Revision ID: 003
Revises: 002
Create Date: 2023-12-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('workplace', sa.String, nullable=False)
    )
    
    # Create cities table
    op.create_table(
        'cities',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String, nullable=False, unique=True)
    )
    
    # Create activities table
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('activity', sa.String, nullable=False),
        sa.Column('type', sa.String, nullable=False)
    )
    
    # Create persons table
    op.create_table(
        'persons',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name_id', sa.Integer, sa.ForeignKey('names.id'), nullable=False),
        sa.Column('age', sa.Integer, nullable=False),
        sa.Column('origin', sa.Integer, sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('children', sa.SmallInteger, nullable=True),
        sa.Column('weekend_activity', sa.String, nullable=True),
        sa.Column('plan_activity', sa.String, nullable=True)
    )


def downgrade():
    op.drop_table('persons')
    op.drop_table('activities')
    op.drop_table('cities')
    op.drop_table('jobs')
