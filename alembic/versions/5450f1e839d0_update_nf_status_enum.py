"""Update NF status enum

Revision ID: 5450f1e839d0
Revises: 1f8dfb2254a4
Create Date: 2025-11-22 10:25:01.049681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5450f1e839d0'
down_revision: Union[str, Sequence[str], None] = '1f8dfb2254a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE nota_fiscal 
        MODIFY COLUMN status 
        ENUM('pendente', 'conferencia', 'liquidacao', 'cancelada') 
        NOT NULL;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        ALTER TABLE nota_fiscal 
        MODIFY COLUMN status 
        ENUM('pendente', 'em_ateste', 'atestada', 'liquidada', 'cancelada') 
        NOT NULL;
        """
    )
