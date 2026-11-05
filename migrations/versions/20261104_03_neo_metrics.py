"""Add normalized NEO metrics."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_03"
down_revision: str | None = "20261104_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("space_observations", sa.Column("is_hazardous", sa.Boolean(), nullable=True))
    op.add_column(
        "space_observations",
        sa.Column("estimated_diameter_meters", sa.Float(), nullable=True),
    )
    op.add_column(
        "space_observations",
        sa.Column("relative_velocity_kps", sa.Float(), nullable=True),
    )
    op.add_column("space_observations", sa.Column("miss_distance_km", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("space_observations", "miss_distance_km")
    op.drop_column("space_observations", "relative_velocity_kps")
    op.drop_column("space_observations", "estimated_diameter_meters")
    op.drop_column("space_observations", "is_hazardous")
