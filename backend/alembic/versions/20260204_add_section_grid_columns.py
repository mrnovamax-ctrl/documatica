"""Add grid_columns, grid_gap, grid_style to page_sections

Revision ID: 20260204_grid
Revises: 4fb063878ac8
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_grid"
down_revision: Union[str, Sequence[str], None] = "4fb063878ac8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "page_sections",
        sa.Column("grid_columns", sa.Integer(), nullable=False, server_default=sa.text("2")),
    )
    op.add_column(
        "page_sections",
        sa.Column("grid_gap", sa.String(length=20), nullable=False, server_default=sa.text("'medium'")),
    )
    op.add_column(
        "page_sections",
        sa.Column("grid_style", sa.String(length=20), nullable=False, server_default=sa.text("'grid'")),
    )


def downgrade() -> None:
    op.drop_column("page_sections", "grid_style")
    op.drop_column("page_sections", "grid_gap")
    op.drop_column("page_sections", "grid_columns")
