"""Add Product nutriscore_grade field

Revision ID: d98171064c5a
Revises: 770709475132
Create Date: 2024-03-03 16:26:02.690921

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d98171064c5a"
down_revision: Union[str, None] = "770709475132"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("products", sa.Column("nutriscore_grade", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("products", "nutriscore_grade")
    # ### end Alembic commands ###
