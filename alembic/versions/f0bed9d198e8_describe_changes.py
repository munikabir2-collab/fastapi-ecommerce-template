"""describe changes

Revision ID: f0bed9d198e8
Revises: a7556d763abd
Create Date: 2026-03-30 07:02:25.482425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0bed9d198e8'
down_revision: Union[str, Sequence[str], None] = 'a7556d763abd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
