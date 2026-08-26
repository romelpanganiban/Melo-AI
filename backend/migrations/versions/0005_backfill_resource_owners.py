"""Backfill owners for resources created before workspace ownership propagation."""

from alembic import op
import sqlalchemy as sa


revision = "0005_backfill_resource_owners"
down_revision = "0004_usage_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    for table in ("sessions", "documents", "knowledge_collections"):
        bind.execute(sa.text(f"""
            UPDATE {table} AS resource
            SET owner_id = membership.user_id
            FROM workspace_members AS membership
            WHERE resource.workspace_id = membership.workspace_id
              AND resource.owner_id IS NULL
              AND membership.role = 'owner'
        """))


def downgrade() -> None:
    pass