"""Add workspace and membership tenancy boundaries."""

from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone
from sqlalchemy import inspect


revision = "0002_workspaces"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    existing_tables = set(inspect(connection).get_table_names())
    if "workspaces" not in existing_tables:
        op.create_table(
            "workspaces",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if "workspace_members" not in existing_tables:
        op.create_table(
            "workspace_members",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    existing_indexes = {item["name"] for item in inspect(connection).get_indexes("workspace_members")}
    for index_name, columns, unique in (
        ("ix_workspace_members_workspace_id", ["workspace_id"], False),
        ("ix_workspace_members_user_id", ["user_id"], False),
        ("ix_workspace_members_workspace_user", ["workspace_id", "user_id"], True),
    ):
        if index_name not in existing_indexes:
            op.create_index(index_name, "workspace_members", columns, unique=unique)

    users = connection.execute(sa.text("SELECT id, email FROM users")).mappings().all()
    member_user_ids = {row[0] for row in connection.execute(sa.text("SELECT user_id FROM workspace_members")).all()}
    for user in users:
        if user["id"] in member_user_ids:
            continue
        workspace_id = str(uuid.uuid4())
        connection.execute(
            sa.text("INSERT INTO workspaces (id, name, created_at) VALUES (:id, :name, :created_at)"),
            {"id": workspace_id, "name": f"{user['email'].split('@')[0]}'s Workspace", "created_at": datetime.now(timezone.utc)},
        )
        connection.execute(
            sa.text("INSERT INTO workspace_members (workspace_id, user_id, role, created_at) VALUES (:workspace_id, :user_id, 'owner', :created_at)"),
            {"workspace_id": workspace_id, "user_id": user["id"], "created_at": datetime.now(timezone.utc)},
        )


def downgrade() -> None:
    op.drop_index("ix_workspace_members_workspace_user", table_name="workspace_members")
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.drop_index("ix_workspace_members_workspace_id", table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")