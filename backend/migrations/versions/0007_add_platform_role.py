"""Add platform_role column to users table.

This migration adds the platform_role field to enable database-backed admin
privilege management instead of relying on ADMIN_EMAIL environment variable
matching.

Revision ID: 0007_add_platform_role
Revises: 0006_phase_14a_document_sharing
Branch labels: None
Depends on: None
"""

import os
from alembic import op
import sqlalchemy as sa


revision = "0007_add_platform_role"
down_revision = "0006_phase_14a_document_sharing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('platform_role', sa.String(20), nullable=False, server_default='user'))
    op.create_index('ix_users_platform_role', 'users', ['platform_role'])
    
    # Set ADMIN_EMAIL user to admin role (one-time migration)
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        connection = op.get_bind()
        connection.execute(
            sa.text("UPDATE users SET platform_role = 'admin' WHERE LOWER(email) = :admin_email"),
            {"admin_email": admin_email}
        )


def downgrade() -> None:
    op.drop_index('ix_users_platform_role', table_name='users')
    op.drop_column('users', 'platform_role')
