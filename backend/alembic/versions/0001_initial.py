"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("city", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "service_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("icon", sa.String(16), nullable=False),
    )

    op.create_table(
        "diagnosis_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("service_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symptom", sa.String(120), nullable=False),
        sa.Column("keywords", sa.Text, nullable=False),
        sa.Column("diagnosis", sa.String(255), nullable=False),
        sa.Column("min_price", sa.Float, nullable=False),
        sa.Column("max_price", sa.Float, nullable=False),
        sa.Column("estimated_minutes", sa.Integer, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False),
    )
    op.create_index("ix_diagnosis_rules_category_id", "diagnosis_rules", ["category_id"])

    op.create_table(
        "technician_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("bio", sa.Text),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("base_rate", sa.Float, nullable=False),
        sa.Column("experience_years", sa.Integer, nullable=False),
        sa.Column("is_available", sa.Boolean, nullable=False),
        sa.Column("verification_status", sa.String(20), nullable=False),
        sa.Column("id_document_type", sa.String(50)),
        sa.Column("id_document_number", sa.String(100)),
        sa.Column("verification_note", sa.Text),
        sa.Column("avg_rating", sa.Float, nullable=False),
        sa.Column("review_count", sa.Integer, nullable=False),
    )
    op.create_index("ix_technician_profiles_city", "technician_profiles", ["city"])
    op.create_index("ix_technician_profiles_verification_status", "technician_profiles", ["verification_status"])

    op.create_table(
        "technician_categories",
        sa.Column("technician_id", sa.Integer, sa.ForeignKey("technician_profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("service_categories.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technician_id", sa.Integer, sa.ForeignKey("technician_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("service_categories.id"), nullable=False),
        sa.Column("problem_description", sa.Text, nullable=False),
        sa.Column("diagnosis", sa.String(255), nullable=False),
        sa.Column("estimated_min_price", sa.Float, nullable=False),
        sa.Column("estimated_max_price", sa.Float, nullable=False),
        sa.Column("estimated_minutes", sa.Integer, nullable=False),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_bookings_customer_id", "bookings", ["customer_id"])
    op.create_index("ix_bookings_technician_id", "bookings", ["technician_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("booking_id", sa.Integer, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technician_id", sa.Integer, sa.ForeignKey("technician_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_reviews_technician_id", "reviews", ["technician_id"])

    op.create_table(
        "saved_technicians",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technician_id", sa.Integer, sa.ForeignKey("technician_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("customer_id", "technician_id", name="uq_saved_customer_technician"),
    )
    op.create_index("ix_saved_technicians_customer_id", "saved_technicians", ["customer_id"])


def downgrade() -> None:
    for table in ("saved_technicians", "reviews", "bookings", "technician_categories", "technician_profiles",
                  "diagnosis_rules", "service_categories", "users"):
        op.drop_table(table)
