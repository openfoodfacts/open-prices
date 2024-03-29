"""add session table

Revision ID: 3c2015517236
Revises: 868640c5012e
Create Date: 2024-01-15 13:50:25.409039

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c2015517236"
down_revision: Union[str, None] = "868640c5012e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Migrate tokens from users to sessions
    op.execute(
        """
        INSERT INTO sessions (user_id, token, created, last_used)
        SELECT user_id, token, created, last_used FROM users
        WHERE token IS NOT NULL
        """
    )
    op.create_index(op.f("ix_sessions_id"), "sessions", ["id"], unique=False)
    op.create_index(op.f("ix_sessions_token"), "sessions", ["token"], unique=True)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.drop_index("ix_users_token", table_name="users")
    op.drop_column("users", "last_used")
    op.drop_column("users", "token")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users", sa.Column("token", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "last_used",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    # Migrate tokens from sessions to users
    op.execute(
        """UPDATE users
        SET token = sessions.token, last_used = sessions.last_used
        FROM sessions
        WHERE sessions.user_id = users.user_id"""
    )
    op.create_index("ix_users_token", "users", ["token"], unique=False)
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_token"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_id"), table_name="sessions")
    op.drop_table("sessions")
    # ### end Alembic commands ###
