"""Create observations schema and idempotency constraint."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261104_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "space_observations" not in inspector.get_table_names():
        op.create_table(
            "space_observations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("source", sa.String(length=80), nullable=False),
            sa.Column("external_id", sa.String(length=120), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("media_type", sa.String(length=40), nullable=True),
            sa.Column("media_url", sa.Text(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("source", "external_id", name="uq_observation_source_external"),
        )
        op.create_index("ix_space_observations_id", "space_observations", ["id"])
        op.create_index("ix_space_observations_source", "space_observations", ["source"])
        op.create_index("ix_space_observations_external_id", "space_observations", ["external_id"])
        op.create_index("ix_space_observations_observed_at", "space_observations", ["observed_at"])
        return

    constraints = {item["name"] for item in inspector.get_unique_constraints("space_observations")}
    if "uq_observation_source_external" not in constraints:
        op.create_unique_constraint(
            "uq_observation_source_external",
            "space_observations",
            ["source", "external_id"],
        )


def downgrade() -> None:
    op.drop_table("space_observations")
