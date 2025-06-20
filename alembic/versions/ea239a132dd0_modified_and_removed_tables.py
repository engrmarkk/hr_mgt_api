"""Modified and Removed Tables

Revision ID: ea239a132dd0
Revises: 471ed2b160a6
Create Date: 2025-05-19 13:52:53.377016

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea239a132dd0"
down_revision: Union[str, None] = "471ed2b160a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("role_side_menu")
    op.drop_table("role_sub_side_menu")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "role_sub_side_menu",
        sa.Column(
            "role_id", sa.VARCHAR(length=50), autoincrement=False, nullable=False
        ),
        sa.Column(
            "sub_side_menu_id",
            sa.VARCHAR(length=50),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="role_sub_side_menu_role_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["sub_side_menu_id"],
            ["sub_side_menu.id"],
            name="role_sub_side_menu_sub_side_menu_id_fkey",
        ),
        sa.PrimaryKeyConstraint(
            "role_id", "sub_side_menu_id", name="role_sub_side_menu_pkey"
        ),
    )
    op.create_table(
        "role_side_menu",
        sa.Column(
            "role_id", sa.VARCHAR(length=50), autoincrement=False, nullable=False
        ),
        sa.Column(
            "side_menu_id", sa.VARCHAR(length=50), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="role_side_menu_role_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["side_menu_id"], ["side_menu.id"], name="role_side_menu_side_menu_id_fkey"
        ),
        sa.PrimaryKeyConstraint("role_id", "side_menu_id", name="role_side_menu_pkey"),
    )
    # ### end Alembic commands ###
