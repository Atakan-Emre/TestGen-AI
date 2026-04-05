"""add json_files type column

Revision ID: 002_json_type
Revises: None
Create Date: 2025-10-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_json_type'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # JSON files tablosuna type kolonu ekle
    op.execute("ALTER TABLE json_files ADD COLUMN IF NOT EXISTS type VARCHAR DEFAULT 'default'")


def downgrade() -> None:
    # Type kolonunu kaldır
    op.drop_column('json_files', 'type')
