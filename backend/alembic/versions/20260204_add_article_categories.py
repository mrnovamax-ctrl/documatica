"""Add article_categories, category_sections, category_blocks

Revision ID: 20260204_cat
Revises: 20260204_parent
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_cat"
down_revision: Union[str, Sequence[str], None] = "20260204_parent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("full_slug", sa.String(length=500), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("meta_title", sa.String(length=255), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("meta_keywords", sa.String(length=500), nullable=True),
        sa.Column("canonical_url", sa.String(length=500), nullable=True),
        sa.Column("layout", sa.String(length=50), nullable=False, server_default=sa.text("'no_sidebar'")),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["article_categories.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_article_categories_full_slug"), "article_categories", ["full_slug"], unique=True)
    op.create_index(op.f("ix_article_categories_id"), "article_categories", ["id"], unique=False)
    op.create_index(op.f("ix_article_categories_parent_id"), "article_categories", ["parent_id"], unique=False)

    op.create_table(
        "category_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("section_type", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("background_style", sa.String(length=100), nullable=False, server_default=sa.text("'light'")),
        sa.Column("css_classes", sa.Text(), nullable=True),
        sa.Column("container_width", sa.String(length=50), nullable=False, server_default=sa.text("'default'")),
        sa.Column("padding_y", sa.String(length=50), nullable=False, server_default=sa.text("'default'")),
        sa.Column("grid_columns", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("grid_gap", sa.String(length=20), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("grid_style", sa.String(length=20), nullable=False, server_default=sa.text("'grid'")),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["article_categories.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_category_sections_category_id"), "category_sections", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_sections_id"), "category_sections", ["id"], unique=False)

    op.create_table(
        "category_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("css_classes", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["section_id"], ["category_sections.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_category_blocks_id"), "category_blocks", ["id"], unique=False)
    op.create_index(op.f("ix_category_blocks_section_id"), "category_blocks", ["section_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_category_blocks_section_id"), table_name="category_blocks")
    op.drop_index(op.f("ix_category_blocks_id"), table_name="category_blocks")
    op.drop_table("category_blocks")
    op.drop_index(op.f("ix_category_sections_id"), table_name="category_sections")
    op.drop_index(op.f("ix_category_sections_category_id"), table_name="category_sections")
    op.drop_table("category_sections")
    op.drop_index(op.f("ix_article_categories_parent_id"), table_name="article_categories")
    op.drop_index(op.f("ix_article_categories_id"), table_name="article_categories")
    op.drop_index(op.f("ix_article_categories_full_slug"), table_name="article_categories")
    op.drop_table("article_categories")
