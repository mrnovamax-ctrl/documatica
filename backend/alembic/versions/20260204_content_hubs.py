"""Content hubs tables

Revision ID: 20260204_hubs
Revises: 20260204_articles
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_hubs"
down_revision: Union[str, Sequence[str], None] = "20260204_articles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_hubs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("meta_title", sa.String(length=255), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("meta_keywords", sa.String(length=500), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_hubs_id"), "content_hubs", ["id"], unique=False)
    op.create_index(op.f("ix_content_hubs_slug"), "content_hubs", ["slug"], unique=True)

    op.create_table(
        "content_hub_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hub_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("meta_title", sa.String(length=255), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("meta_keywords", sa.String(length=500), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["hub_id"], ["content_hubs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hub_id", "slug", name="uq_content_hub_section_hub_slug"),
    )
    op.create_index(op.f("ix_content_hub_sections_hub_id"), "content_hub_sections", ["hub_id"], unique=False)
    op.create_index(op.f("ix_content_hub_sections_id"), "content_hub_sections", ["id"], unique=False)

    op.create_table(
        "hub_section_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["content_hub_sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "article_id", name="uq_hub_section_article_section_article"),
    )
    op.create_index(op.f("ix_hub_section_articles_article_id"), "hub_section_articles", ["article_id"], unique=False)
    op.create_index(op.f("ix_hub_section_articles_id"), "hub_section_articles", ["id"], unique=False)
    op.create_index(op.f("ix_hub_section_articles_section_id"), "hub_section_articles", ["section_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hub_section_articles_section_id"), table_name="hub_section_articles")
    op.drop_index(op.f("ix_hub_section_articles_id"), table_name="hub_section_articles")
    op.drop_index(op.f("ix_hub_section_articles_article_id"), table_name="hub_section_articles")
    op.drop_table("hub_section_articles")
    op.drop_index(op.f("ix_content_hub_sections_id"), table_name="content_hub_sections")
    op.drop_index(op.f("ix_content_hub_sections_hub_id"), table_name="content_hub_sections")
    op.drop_table("content_hub_sections")
    op.drop_index(op.f("ix_content_hubs_slug"), table_name="content_hubs")
    op.drop_index(op.f("ix_content_hubs_id"), table_name="content_hubs")
    op.drop_table("content_hubs")
