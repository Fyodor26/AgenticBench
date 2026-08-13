"""Create agent, task, and evaluation models

Revision ID: 002_create_agent_task_evaluation
Revises: 001_create_initial_models
Create Date: 2024-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_create_agent_task_evaluation'
down_revision = 'e2e1e626c328'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('api_endpoint', sa.String(500), nullable=False),
        sa.Column('api_key', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=True)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)
    op.create_index(op.f('ix_tasks_category'), 'tasks', ['category'], unique=False)
    op.create_index(op.f('ix_tasks_created_by'), 'tasks', ['created_by'], unique=False)

    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('agent_response', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_task_id'), 'evaluations', ['task_id'], unique=False)
    op.create_index(op.f('ix_evaluations_agent_id'), 'evaluations', ['agent_id'], unique=False)

    # Create evaluation_metrics table
    op.create_table(
        'evaluation_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('correctness_score', sa.Float(), nullable=False),
        sa.Column('hallucination_score', sa.Float(), nullable=False),
        sa.Column('tool_usage_score', sa.Float(), nullable=False),
        sa.Column('planning_quality_score', sa.Float(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('evaluation_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_metrics_evaluation_id'), 'evaluation_metrics', ['evaluation_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluation_metrics_evaluation_id'), table_name='evaluation_metrics')
    op.drop_table('evaluation_metrics')
    op.drop_index(op.f('ix_evaluations_agent_id'), table_name='evaluations')
    op.drop_index(op.f('ix_evaluations_task_id'), table_name='evaluations')
    op.drop_table('evaluations')
    op.drop_index(op.f('ix_tasks_created_by'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_category'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_title'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_agents_name'), table_name='agents')
    op.drop_table('agents')
