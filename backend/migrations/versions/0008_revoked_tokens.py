"""Add revoked_tokens table for durable token revocation.

This migration creates the database-backed revoked_tokens table used by the auth
service to reject revoked bearer tokens after logout or explicit revocation.

Revision ID: 0008_revoked_tokens
Revises: 0007_add_platform_role
Branch labels: None
Depends on: None
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_revoked_tokens"
down_revision = "0007_add_platform_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_revoked_tokens_token_hash', 'revoked_tokens', ['token_hash'], unique=True)
    op.create_index('ix_revoked_tokens_user_id', 'revoked_tokens', ['user_id'])
    op.create_index('ix_revoked_tokens_expires_at', 'revoked_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_revoked_tokens_expires_at', table_name='revoked_tokens')
    op.drop_index('ix_revoked_tokens_user_id', table_name='revoked_tokens')
    op.drop_index('ix_revoked_tokens_token_hash', table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
