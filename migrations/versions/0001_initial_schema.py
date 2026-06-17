"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("logistics", sa.Text(), nullable=False),
        sa.Column("after_sales", sa.Text(), nullable=False),
    )
    op.create_table(
        "faqs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("keyword", sa.String(length=80), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=160), nullable=False),
    )
    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.String(length=80), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.conversation_id"]),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("knowledge_chunks")
    op.drop_table("faqs")
    op.drop_table("orders")
    op.drop_table("products")
