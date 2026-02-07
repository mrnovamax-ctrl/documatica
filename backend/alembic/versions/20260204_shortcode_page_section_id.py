"""Add page_section_id to shortcodes, nullable section_type/blocks

Revision ID: 20260204_shortcode
Revises: 20260204_cat
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_shortcode"
down_revision: Union[str, Sequence[str], None] = "20260204_cat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shortcodes",
        sa.Column("page_section_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_shortcodes_page_section_id",
        "shortcodes",
        "page_sections",
        ["page_section_id"],
        ["id"],
    )
    op.create_index(op.f("ix_shortcodes_page_section_id"), "shortcodes", ["page_section_id"], unique=False)
    op.alter_column(
        "shortcodes",
        "section_type",
        existing_type=sa.String(100),
        nullable=True,
    )
    op.alter_column(
        "shortcodes",
        "blocks",
        existing_type=sa.JSON(),
        nullable=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shortcodes_page_section_id"), table_name="shortcodes")
    op.drop_constraint("fk_shortcodes_page_section_id", "shortcodes", type_="foreignkey")
    op.drop_column("shortcodes", "page_section_id")
    op.alter_column(
        "shortcodes",
        "section_type",
        existing_type=sa.String(100),
        nullable=False,
    )
    op.alter_column(
        "shortcodes",
        "blocks",
        existing_type=sa.JSON(),
        nullable=False,
    )
