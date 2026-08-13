"""Add provider, model, and enhanced fields to agents and evaluations

Revision ID: 002_enhanced_agents_evaluations
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_enhanced_agents_evaluations'
down_revision = '002_create_agent_task_evaluation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to agents table
    op.add_column('agents', sa.Column('provider', sa.String(50), nullable=False, server_default='generic'))
    op.add_column('agents', sa.Column('model', sa.String(255), nullable=True))
    op.add_column('agents', sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'))
    op.add_column('agents', sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='2048'))
    op.add_column('agents', sa.Column('timeout', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('agents', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Make api_endpoint and api_key nullable
    op.alter_column('agents', 'api_endpoint', existing_type=sa.String(500), nullable=True)
    op.alter_column('agents', 'api_key', existing_type=sa.String(500), nullable=True)
    
    # Add index for active agents
    op.create_index('ix_agents_is_active', 'agents', ['is_active'])
    op.create_index('ix_agents_provider', 'agents', ['provider'])
    
    # Add columns to evaluations table
    op.add_column('evaluations', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('evaluations', sa.Column('evaluation_metadata', sa.JSON(), nullable=True))
    
    # Add status index
    op.create_index('ix_evaluations_status', 'evaluations', ['status'])
    op.create_index('ix_evaluations_created_at', 'evaluations', ['created_at'])
    
    # Add composite indexes
    op.create_index('ix_eval_agent_created', 'evaluations', ['agent_id', 'created_at'])
    op.create_index('ix_eval_task_status', 'evaluations', ['task_id', 'status'])
    
    # Update evaluation_metrics table
    op.add_column('evaluation_metrics', sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('evaluation_metrics', sa.Column('execution_time', sa.Float(), nullable=True))
    op.add_column('evaluation_metrics', sa.Column('tokens_used', sa.Integer(), nullable=True))
    
    # Add index on metrics score
    op.create_index('ix_metrics_score', 'evaluation_metrics', ['overall_score'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_metrics_score', table_name='evaluation_metrics')
    op.drop_index('ix_eval_task_status', table_name='evaluations')
    op.drop_index('ix_eval_agent_created', table_name='evaluations')
    op.drop_index('ix_evaluations_created_at', table_name='evaluations')
    op.drop_index('ix_evaluations_status', table_name='evaluations')
    op.drop_index('ix_agents_provider', table_name='agents')
    op.drop_index('ix_agents_is_active', table_name='agents')
    
    # Remove columns from agents table
    op.drop_column('agents', 'is_active')
    op.drop_column('agents', 'timeout')
    op.drop_column('agents', 'max_tokens')
    op.drop_column('agents', 'temperature')
    op.drop_column('agents', 'model')
    op.drop_column('agents', 'provider')
    
    # Revert nullable changes
    op.alter_column('agents', 'api_endpoint', existing_type=sa.String(500), nullable=False)
    op.alter_column('agents', 'api_key', existing_type=sa.String(500), nullable=False)
    
    # Remove columns from evaluations table
    op.drop_column('evaluations', 'evaluation_metadata')
    op.drop_column('evaluations', 'retry_count')
    
    # Remove columns from evaluation_metrics table
    op.drop_column('evaluation_metrics', 'tokens_used')
    op.drop_column('evaluation_metrics', 'execution_time')
    op.drop_column('evaluation_metrics', 'cost')
