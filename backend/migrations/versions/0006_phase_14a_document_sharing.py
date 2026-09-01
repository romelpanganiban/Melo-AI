"""Phase 14a: Add document sharing policy with is_shared column.

This migration adds the is_shared flag to the Document model for Phase 14a
(Central Authorization Middleware). The flag enables per-document sharing:
- Owner can always access
- Non-owners can access only if is_shared=True

Existing documents default to is_shared=False (private).
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_phase_14a_document_sharing"
down_revision = "0005_backfill_resource_owners"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index('ix_documents_is_shared', 'documents', ['is_shared'])


def downgrade() -> None:
    op.drop_index('ix_documents_is_shared', table_name='documents')
    op.drop_column('documents', 'is_shared')
