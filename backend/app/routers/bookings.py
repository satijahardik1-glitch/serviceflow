from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user, require_roles
from app.core.pagination import PageParams, paginate
from app.db.session import get_db
from app.models import Booking, Review, TechnicianProfile, User
from app.schemas.booking import BookingCreate, BookingOut, BookingStatusUpdate, ReviewCreate, booking_out
from app.services.diagnosis import diagnose
from app.services.ratings import recompute_rating

router = APIRouter(prefix="/bookings", tags=["bookings"])

# role -> {current status: allowed next statuses}
TECHNICIAN_TRANSITIONS = {
    "pending": {"accepted", "rejected"},
    "accepted": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
}
CUSTOMER_TRANSITIONS = {"pending": {"cancelled"}, "accepted": {"cancelled"}}
ACTIVE_STATUSES = ("accepted", "in_progress")
JOB_WINDOW = timedelta(hours=2)


def load_options():
    return (
        selectinload(Booking.customer),
        selectinload(Booking.technician).selectinload(TechnicianProfile.user),
        selectinload(Booking.category),
        selectinload(Booking.review).selectinload(Review.customer),
    )


def _get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.scalar(select(Booking).options(*load_options()).where(Booking.id == booking_id))
    if booking is None:
        raise HTTPException(404, "Booking not found")
    return booking


def _utc(dt: datetime) -> datetime:
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _lock_technician(db: Session, technician_id: int) -> Optional[TechnicianProfile]:
    """Row-level lock (SELECT ... FOR UPDATE) so concurrent requests for one technician are serialised."""
    return db.scalar(select(TechnicianProfile).where(TechnicianProfile.id == technician_id).with_for_update())


def _has_conflict(db: Session, technician_id: int, when: datetime, exclude_id: Optional[int] = None) -> bool:
    stmt = select(Booking.id).where(
        Booking.technician_id == technician_id, Booking.status.in_(ACTIVE_STATUSES),
        Booking.scheduled_at > when - JOB_WINDOW, Booking.scheduled_at < when + JOB_WINDOW)
    if exclude_id is not None:
        stmt = stmt.where(Booking.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def _ensure_participant(booking: Booking, user: User) -> None:
    allowed = user.role == "admin" or booking.customer_id == user.id or booking.technician.user_id == user.id
    if not allowed:
        raise HTTPException(403, "You do not have access to this booking")


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(data: BookingCreate, user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    tech = _lock_technician(db, data.technician_id)
    if tech is None or tech.verification_status != "verified" or not tech.user.is_active:
        raise HTTPException(404, "Technician not found or not verified")
    if not tech.is_available:
        raise HTTPException(409, "This technician is currently unavailable")
    if data.category_id not in {c.id for c in tech.categories}:
        raise HTTPException(400, "This technician does not offer the selected service")

    when = _utc(data.scheduled_at)
    if when <= datetime.now(timezone.utc) + timedelta(minutes=30):
        raise HTTPException(422, "Please choose a time at least 30 minutes from now")
    if _has_conflict(db, tech.id, when):
        raise HTTPException(409, "The technician already has a confirmed job around that time. Pick another slot.")

    try:
        est = diagnose(db, data.category_id, data.problem_description, data.symptoms)
    except LookupError as exc:
        raise HTTPException(400, str(exc))

    booking = Booking(
        customer_id=user.id, technician_id=tech.id, category_id=data.category_id,
        problem_description=data.problem_description.strip(), diagnosis=est.diagnosis,
        estimated_min_price=est.min_price, estimated_max_price=est.max_price,
        estimated_minutes=est.estimated_minutes, address=data.address.strip(), city=data.city.strip(),
        scheduled_at=when, status="pending",
    )
    db.add(booking)
    db.commit()
    return booking_out(_get_booking(db, booking.id))


@router.get("/mine", response_model=list[BookingOut])
def my_bookings(
    response: Response,
    status_filter: Optional[str] = None,
    page: PageParams = Depends(),
    user: User = Depends(require_roles("customer", "technician")),
    db: Session = Depends(get_db),
):
    stmt = select(Booking).options(*load_options()).order_by(Booking.scheduled_at.desc(), Booking.id.desc())
    if user.role == "customer":
        stmt = stmt.where(Booking.customer_id == user.id)
    else:
        profile = db.scalar(select(TechnicianProfile).where(TechnicianProfile.user_id == user.id))
        if profile is None:
            response.headers["X-Total-Count"] = "0"
            return []
        stmt = stmt.where(Booking.technician_id == profile.id)
    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)
    return [booking_out(b) for b in paginate(db, stmt, response, page)]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = _get_booking(db, booking_id)
    _ensure_participant(booking, user)
    return booking_out(booking)


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_status(
    booking_id: int,
    data: BookingStatusUpdate,
    user: User = Depends(require_roles("customer", "technician")),
    db: Session = Depends(get_db),
):
    booking = _get_booking(db, booking_id)
    _ensure_participant(booking, user)
    _lock_technician(db, booking.technician_id)  # serialise status changes per technician
    db.refresh(booking, attribute_names=["status"])  # re-read after acquiring the lock

    transitions = CUSTOMER_TRANSITIONS if user.role == "customer" else TECHNICIAN_TRANSITIONS
    if data.status not in transitions.get(booking.status, set()):
        raise HTTPException(409, f"Cannot change a booking from '{booking.status}' to '{data.status}'")
    if data.status == "accepted" and _has_conflict(db, booking.technician_id, _utc(booking.scheduled_at), booking.id):
        raise HTTPException(409, "You already have a confirmed job around that time. Reject or reschedule one of them.")
    booking.status = data.status
    db.commit()
    return booking_out(_get_booking(db, booking_id))


@router.post("/{booking_id}/review", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def add_review(booking_id: int, data: ReviewCreate, user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    booking = _get_booking(db, booking_id)
    if booking.customer_id != user.id:
        raise HTTPException(403, "You can only review your own bookings")
    if booking.status != "completed":
        raise HTTPException(409, "You can review a booking only after it is completed")
    if booking.review is not None:
        raise HTTPException(409, "You have already reviewed this booking")
    db.add(Review(booking_id=booking.id, customer_id=user.id, technician_id=booking.technician_id,
                  rating=data.rating, comment=(data.comment or "").strip() or None))
    try:
        db.flush()
        recompute_rating(db, booking.technician_id)
        db.commit()
    except IntegrityError:  # concurrent duplicate review (unique booking_id)
        db.rollback()
        raise HTTPException(409, "You have already reviewed this booking")
    return booking_out(_get_booking(db, booking_id))
