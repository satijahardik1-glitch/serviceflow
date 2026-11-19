from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models import Booking
from app.schemas.technician import ReviewOut


class BookingCreate(BaseModel):
    technician_id: int
    category_id: int
    problem_description: str = Field(min_length=5, max_length=2000)
    symptoms: list[str] = []
    address: str = Field(min_length=5, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    scheduled_at: datetime


class BookingStatusUpdate(BaseModel):
    status: Literal["accepted", "rejected", "in_progress", "completed", "cancelled"]


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class BookingOut(BaseModel):
    id: int
    status: str
    customer_id: int
    customer_name: str
    customer_phone: Optional[str] = None
    technician_id: int
    technician_name: str
    category_id: int
    category_name: str
    problem_description: str
    diagnosis: str
    estimated_min_price: float
    estimated_max_price: float
    estimated_minutes: int
    address: str
    city: str
    scheduled_at: datetime
    created_at: datetime
    review: Optional[ReviewOut] = None


def review_out(r) -> ReviewOut:
    return ReviewOut(id=r.id, rating=r.rating, comment=r.comment, customer_name=r.customer.name, created_at=r.created_at)


def booking_out(b: Booking) -> BookingOut:
    # customer phone is only shared once the technician has accepted the job
    share_phone = b.status in ("accepted", "in_progress", "completed")
    return BookingOut(
        id=b.id, status=b.status, customer_id=b.customer_id, customer_name=b.customer.name,
        customer_phone=b.customer.phone if share_phone else None,
        technician_id=b.technician_id, technician_name=b.technician.user.name,
        category_id=b.category_id, category_name=b.category.name,
        problem_description=b.problem_description, diagnosis=b.diagnosis,
        estimated_min_price=b.estimated_min_price, estimated_max_price=b.estimated_max_price,
        estimated_minutes=b.estimated_minutes, address=b.address, city=b.city,
        scheduled_at=b.scheduled_at, created_at=b.created_at,
        review=review_out(b.review) if b.review else None,
    )
