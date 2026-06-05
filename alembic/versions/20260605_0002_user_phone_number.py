from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260605_0002"
down_revision = "20260605_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.Text(), nullable=True))
    op.execute(
        """
        WITH numbered_users AS (
            SELECT id, '+7' || LPAD(ROW_NUMBER() OVER (ORDER BY created_at, id)::text, 10, '0') AS generated_phone
            FROM users
            WHERE phone_number IS NULL
        )
        UPDATE users
        SET phone_number = numbered_users.generated_phone
        FROM numbered_users
        WHERE users.id = numbered_users.id
        """
    )
    op.alter_column("users", "phone_number", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "phone_number")
