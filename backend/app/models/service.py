from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(16), default="🛠️")

    rules: Mapped[list["DiagnosisRule"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class DiagnosisRule(Base):
    __tablename__ = "diagnosis_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id", ondelete="CASCADE"), index=True)
    symptom: Mapped[str] = mapped_column(String(120))  # short label shown as a selectable chip
    keywords: Mapped[str] = mapped_column(Text, default="")  # comma separated, lower case
    diagnosis: Mapped[str] = mapped_column(String(255))
    min_price: Mapped[float] = mapped_column(Float)
    max_price: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # tie-breaker (safety-critical rules rank higher)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # fallback when nothing matches

    category: Mapped[ServiceCategory] = relationship(back_populates="rules")
