"""Add monthly token usage ledger."""

from alembic import op
import sqlalchemy as sa


revision = "0004_usage_ledger"
down_revision = "0003_resource_workspaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_ledger_workspace_id", "usage_ledger", ["workspace_id"], unique=False)
    op.create_index("ix_usage_ledger_user_id", "usage_ledger", ["user_id"], unique=False)
    op.create_index("ix_usage_ledger_period_start", "usage_ledger", ["period_start"], unique=False)
    op.create_index("ix_usage_ledger_workspace_user_period", "usage_ledger", ["workspace_id", "user_id", "period_start"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_usage_ledger_workspace_user_period", table_name="usage_ledger")
    op.drop_index("ix_usage_ledger_period_start", table_name="usage_ledger")
    op.drop_index("ix_usage_ledger_user_id", table_name="usage_ledger")
    op.drop_index("ix_usage_ledger_workspace_id", table_name="usage_ledger")
    op.drop_table("usage_ledger")