from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.service import ServiceCategory
from app.models.user import TechnicianProfile, User


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technician_profiles.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))
    problem_description: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str] = mapped_column(String(255))
    estimated_min_price: Mapped[float] = mapped_column(Float)
    estimated_max_price: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    technician: Mapped[TechnicianProfile] = relationship(foreign_keys=[technician_id])
    category: Mapped[ServiceCategory] = relationship()
    review: Mapped[Optional["Review"]] = relationship(back_populates="booking", uselist=False)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technician_profiles.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped[Booking] = relationship(back_populates="review")
    customer: Mapped[User] = relationship()


class SavedTechnician(Base):
    __tablename__ = "saved_technicians"
    __table_args__ = (UniqueConstraint("customer_id", "technician_id", name="uq_saved_customer_technician"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technician_profiles.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
