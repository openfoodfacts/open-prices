"""Add Product labels_tags field

Revision ID: 770709475132
Revises: d2d14a95ae1c
Create Date: 2024-02-15 11:49:43.242694

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "770709475132"
down_revision: Union[str, None] = "d2d14a95ae1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "products",
        sa.Column(
            "labels_tags",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_products_labels_tags"), "products", ["labels_tags"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_products_labels_tags"), table_name="products")
    op.drop_column("products", "labels_tags")
    # ### end Alembic commands ###