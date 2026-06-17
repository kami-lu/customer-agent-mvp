"""add support tickets

Revision ID: 0003_add_tickets
Revises: 0002_add_users_and_tokens
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_tickets"
down_revision = "0002_add_users_and_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.String(length=80), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.conversation_id"]),
    )
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])
    op.create_index("ix_tickets_conversation_id", "tickets", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_conversation_id", table_name="tickets")
    op.drop_index("ix_tickets_user_id", table_name="tickets")
    op.drop_table("tickets")
