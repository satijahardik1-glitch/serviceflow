"""encrypt technician ID document numbers at rest

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa

from app.core.crypto import TOKEN_PREFIX, decrypt, encrypt

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("technician_profiles") as batch:
        batch.alter_column("id_document_number", existing_type=sa.String(100), type_=sa.Text(), existing_nullable=True)
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, id_document_number FROM technician_profiles WHERE id_document_number IS NOT NULL")).fetchall()
    for row_id, value in rows:
        if not value.startswith(TOKEN_PREFIX):
            conn.execute(sa.text("UPDATE technician_profiles SET id_document_number = :v WHERE id = :i"),
                         {"v": encrypt(value), "i": row_id})


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, id_document_number FROM technician_profiles WHERE id_document_number IS NOT NULL")).fetchall()
    for row_id, value in rows:
        plain = (decrypt(value) or "")[:100]
        conn.execute(sa.text("UPDATE technician_profiles SET id_document_number = :v WHERE id = :i"), {"v": plain or None, "i": row_id})
    with op.batch_alter_table("technician_profiles") as batch:
        batch.alter_column("id_document_number", existing_type=sa.Text(), type_=sa.String(100), existing_nullable=True)
