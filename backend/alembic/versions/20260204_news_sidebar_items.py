"""News sidebar items table

Revision ID: 20260204_news_sidebar
Revises: 20260204_shortcode
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_news_sidebar"
down_revision: Union[str, Sequence[str], None] = "20260204_shortcode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_sidebar_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("block_type", sa.String(50), nullable=False),
        sa.Column("shortcode_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_news_sidebar_items_shortcode_id",
        "news_sidebar_items",
        "shortcodes",
        ["shortcode_id"],
        ["id"],
    )
    op.create_index(op.f("ix_news_sidebar_items_shortcode_id"), "news_sidebar_items", ["shortcode_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_news_sidebar_items_shortcode_id"), table_name="news_sidebar_items")
    op.drop_constraint("fk_news_sidebar_items_shortcode_id", "news_sidebar_items", type_="foreignkey")
    op.drop_table("news_sidebar_items")
