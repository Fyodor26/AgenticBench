"""Add is_active field to tasks table

Revision ID: 003_add_task_is_active
Revises: 002_enhanced_agents_evaluations
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_task_is_active'
down_revision = '002_enhanced_agents_evaluations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to tasks
    op.add_column('tasks', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.create_index('ix_tasks_is_active', 'tasks', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_tasks_is_active', table_name='tasks')
    op.drop_column('tasks', 'is_active')
