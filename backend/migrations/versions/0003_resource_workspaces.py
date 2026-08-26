"""Move existing owned resources into their user's default workspace."""

from alembic import op
import sqlalchemy as sa

revision = "0003_resource_workspaces"
down_revision = "0002_workspaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in ("sessions", "documents", "knowledge_collections", "study_progress"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "workspace_id" not in columns:
            op.add_column(table, sa.Column("workspace_id", sa.String(length=36), nullable=True))
            op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"], unique=False)

    bind.execute(sa.text("UPDATE sessions SET workspace_id = (SELECT wm.workspace_id FROM workspace_members wm WHERE wm.user_id = sessions.owner_id) WHERE workspace_id IS NULL AND owner_id IS NOT NULL"))
    bind.execute(sa.text("UPDATE documents SET workspace_id = (SELECT wm.workspace_id FROM workspace_members wm WHERE wm.user_id = documents.owner_id) WHERE workspace_id IS NULL AND owner_id IS NOT NULL"))
    bind.execute(sa.text("UPDATE knowledge_collections SET workspace_id = (SELECT wm.workspace_id FROM workspace_members wm WHERE wm.user_id = knowledge_collections.owner_id) WHERE workspace_id IS NULL AND owner_id IS NOT NULL"))
    bind.execute(sa.text("UPDATE study_progress SET workspace_id = (SELECT s.workspace_id FROM sessions s WHERE s.id = study_progress.session_id) WHERE workspace_id IS NULL"))


def downgrade() -> None:
    for table in ("study_progress", "knowledge_collections", "documents", "sessions"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_column(table, "workspace_id")