"""learner_profiles.default_session_minutes for settings

Revision ID: 0021_profile_session_minutes
Revises: 0020_product_events_views
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_profile_session_minutes"
down_revision: Union[str, Sequence[str], None] = "0020_product_events_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learner_profiles",
        sa.Column(
            "default_session_minutes",
            sa.Integer(),
            nullable=False,
            server_default="25",
        ),
    )
    op.create_check_constraint(
        "ck_learner_profiles_default_session_minutes",
        "learner_profiles",
        "default_session_minutes >= 5 AND default_session_minutes <= 180",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_learner_profiles_default_session_minutes",
        "learner_profiles",
        type_="check",
    )
    op.drop_column("learner_profiles", "default_session_minutes")
