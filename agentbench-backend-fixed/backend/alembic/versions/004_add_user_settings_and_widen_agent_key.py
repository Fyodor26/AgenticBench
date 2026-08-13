"""Add user_settings table; widen agents.api_key for encrypted values

Revision ID: 004_add_user_settings
Revises: 003_add_task_is_active
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_user_settings'
down_revision = '003_add_task_is_active'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('ollama_base_url', sa.String(length=500), nullable=False, server_default='http://localhost:11434'),
        sa.Column('gemini_api_key_encrypted', sa.String(length=1000), nullable=True),
        sa.Column('openai_api_key_encrypted', sa.String(length=1000), nullable=True),
        sa.Column('judge_model', sa.String(length=50), nullable=False, server_default='gemini'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='2048'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])

    # Agent api_key was String(500); encrypted (Fernet) values are longer
    # than the raw plaintext they replace, so this widens the column to
    # avoid truncation. Existing plaintext rows keep working - they're
    # simply treated as legacy/unencrypted until next update
    # (see app.core.security.decrypt_secret's fail-safe behavior).
    op.alter_column('agents', 'api_key', type_=sa.String(length=1000))


def downgrade() -> None:
    op.alter_column('agents', 'api_key', type_=sa.String(length=500))
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')
