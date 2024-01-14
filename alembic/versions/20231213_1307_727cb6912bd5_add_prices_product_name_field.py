"""Add prices product_name field

Revision ID: 727cb6912bd5
Revises: cce1da5c6733
Create Date: 2023-12-13 13:07:56.309158

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "727cb6912bd5"
down_revision: Union[str, None] = "cce1da5c6733"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("prices", sa.Column("product_name", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("prices", "product_name")
    # ### end Alembic commands ###