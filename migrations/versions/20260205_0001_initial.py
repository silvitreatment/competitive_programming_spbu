"""initial

Revision ID: 20260205_0001
Revises: 
Create Date: 2026-02-05 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260205_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "article",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("author_name", sa.String(length=200), nullable=True),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("telegram_username", sa.String(length=200), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "comment",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("article.id"), nullable=False),
        sa.Column("author_name", sa.String(length=200), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_comment_article_id", "comment", ["article_id"], unique=False)
    op.create_table(
        "review",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("contact_slug", sa.String(length=100), nullable=False),
        sa.Column("author_name", sa.String(length=200), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_review_contact_slug", "review", ["contact_slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_contact_slug", table_name="review")
    op.drop_table("review")
    op.drop_index("ix_comment_article_id", table_name="comment")
    op.drop_table("comment")
    op.drop_table("user")
    op.drop_table("article")
