"""add prices.category_tag field

Revision ID: 5acb37b190cc
Revises: 7103fb49908f
Create Date: 2023-11-23 08:28:39.136672

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5acb37b190cc"
down_revision: Union[str, None] = "7103fb49908f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("prices", sa.Column("category_tag", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_prices_category_tag"), "prices", ["category_tag"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_prices_category_tag"), table_name="prices")
    op.drop_column("prices", "category_tag")
    # ### end Alembic commands ###
