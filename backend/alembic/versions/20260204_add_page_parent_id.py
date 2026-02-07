"""Add parent_id to pages for hierarchy (e.g. /upd/ and /upd/ooo/)

Revision ID: 20260204_parent
Revises: 20260204_grid
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260204_parent"
down_revision: Union[str, Sequence[str], None] = "20260204_grid"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pages",
        sa.Column("parent_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_pages_parent_id",
        "pages",
        "pages",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_pages_parent_id"), "pages", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pages_parent_id"), table_name="pages")
    op.drop_constraint("fk_pages_parent_id", "pages", type_="foreignkey")
    op.drop_column("pages", "parent_id")
