from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.crypto import decrypt, mask
from app.models import TechnicianProfile
from app.schemas.service import CategoryOut


class TechnicianPublic(BaseModel):
    id: int
    user_id: int
    name: str
    city: str
    bio: Optional[str] = None
    categories: list[CategoryOut]
    base_rate: float
    experience_years: int
    is_available: bool
    verification_status: str
    avg_rating: float
    review_count: int


class MatchedTechnician(TechnicianPublic):
    score: float
    reasons: list[str]


class ReviewOut(BaseModel):
    id: int
    rating: int
    comment: Optional[str] = None
    customer_name: str
    created_at: datetime


class TechnicianDetail(TechnicianPublic):
    reviews: list[ReviewOut]
    is_saved: bool = False


class TechnicianSelf(TechnicianPublic):
    email: str
    phone: Optional[str] = None
    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    verification_note: Optional[str] = None


class TechnicianProfileUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=2000)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    base_rate: Optional[float] = Field(default=None, ge=0)
    experience_years: Optional[int] = Field(default=None, ge=0, le=60)
    category_ids: Optional[list[int]] = None
    id_document_type: Optional[str] = Field(default=None, max_length=50)
    id_document_number: Optional[str] = Field(default=None, max_length=100)


class AvailabilityUpdate(BaseModel):
    is_available: bool


def public_fields(p: TechnicianProfile) -> dict:
    return dict(
        id=p.id, user_id=p.user_id, name=p.user.name, city=p.city, bio=p.bio,
        categories=[CategoryOut.model_validate(c) for c in p.categories],
        base_rate=p.base_rate, experience_years=p.experience_years, is_available=p.is_available,
        verification_status=p.verification_status, avg_rating=p.avg_rating, review_count=p.review_count,
    )


def tech_public(p: TechnicianProfile) -> TechnicianPublic:
    return TechnicianPublic(**public_fields(p))


def tech_self(p: TechnicianProfile, reveal: bool = False) -> TechnicianSelf:
    """reveal=True (admin review only) returns the decrypted ID number; otherwise it is masked."""
    return TechnicianSelf(
        **public_fields(p), email=p.user.email, phone=p.user.phone,
        id_document_type=p.id_document_type,
        id_document_number=decrypt(p.id_document_number) if reveal else mask(p.id_document_number),
        verification_note=p.verification_note,
    )
