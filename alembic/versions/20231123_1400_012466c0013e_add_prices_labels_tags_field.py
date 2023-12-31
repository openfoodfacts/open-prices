"""add prices.labels_tags field

Revision ID: 012466c0013e
Revises: 5acb37b190cc
Create Date: 2023-11-23 14:00:14.162599

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012466c0013e"
down_revision: Union[str, None] = "5acb37b190cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "prices",
        sa.Column(
            "labels_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.create_index(
        op.f("ix_prices_labels_tags"), "prices", ["labels_tags"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_prices_labels_tags"), table_name="prices")
    op.drop_column("prices", "labels_tags")
    # ### end Alembic commands ###
