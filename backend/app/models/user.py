from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

technician_categories = Table(
    "technician_categories",
    Base.metadata,
    Column("technician_id", ForeignKey("technician_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("service_categories.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="customer", index=True)  # customer|technician|admin
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    technician_profile: Mapped[Optional["TechnicianProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class TechnicianProfile(Base):
    __tablename__ = "technician_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    base_rate: Mapped[float] = mapped_column(Float, default=0)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|verified|rejected
    id_document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    id_document_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    verification_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avg_rating: Mapped[float] = mapped_column(Float, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="technician_profile")
    categories = relationship("ServiceCategory", secondary=technician_categories, lazy="selectin")
