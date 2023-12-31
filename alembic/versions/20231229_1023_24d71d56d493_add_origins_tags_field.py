"""add origins_tags field

Revision ID: 24d71d56d493
Revises: 1e60d73e79cd
Create Date: 2023-12-29 10:23:22.430506

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24d71d56d493"
down_revision: Union[str, None] = "1e60d73e79cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "prices",
        sa.Column(
            "origins_tags",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_prices_origins_tags"), "prices", ["origins_tags"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_prices_origins_tags"), table_name="prices")
    op.drop_column("prices", "origins_tags")
    # ### end Alembic commands ###
