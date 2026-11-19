from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.crypto import decrypt, encrypt
from app.core.deps import get_optional_user, require_roles
from app.db.session import get_db
from app.models import Review, SavedTechnician, ServiceCategory, TechnicianProfile, User
from app.schemas.booking import review_out
from app.schemas.technician import (
    AvailabilityUpdate, MatchedTechnician, TechnicianDetail, TechnicianProfileUpdate, TechnicianPublic,
    TechnicianSelf, public_fields, tech_public, tech_self,
)
from app.services.matching import match_technicians

router = APIRouter(prefix="/technicians", tags=["technicians"])


def _own_profile(db: Session, user: User) -> TechnicianProfile:
    profile = db.scalar(select(TechnicianProfile).where(TechnicianProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(404, "Technician profile not found")
    return profile


@router.get("/match", response_model=list[MatchedTechnician])
def match(
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    available_only: bool = False,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Smart matching: verified technicians filtered by skill and ranked by a transparent score."""
    ranked = match_technicians(db, category_id, city, available_only, limit)
    return [MatchedTechnician(**public_fields(t), score=score, reasons=reasons) for t, score, reasons in ranked]


@router.get("/me", response_model=TechnicianSelf)
def my_profile(user: User = Depends(require_roles("technician")), db: Session = Depends(get_db)):
    return tech_self(_own_profile(db, user))


@router.put("/me", response_model=TechnicianSelf)
def update_my_profile(
    data: TechnicianProfileUpdate,
    user: User = Depends(require_roles("technician")),
    db: Session = Depends(get_db),
):
    profile = _own_profile(db, user)
    changes = data.model_dump(exclude_unset=True)

    if "category_ids" in changes:
        ids = set(changes.pop("category_ids") or [])
        if not ids:
            raise HTTPException(422, "Select at least one service category")
        cats = list(db.scalars(select(ServiceCategory).where(ServiceCategory.id.in_(ids))).all())
        if len(cats) != len(ids):
            raise HTTPException(422, "One or more service categories are invalid")
        profile.categories = cats
    if "phone" in changes:
        user.phone = changes.pop("phone")

    id_changed = False
    if "id_document_number" in changes:
        raw = (changes.pop("id_document_number") or "").strip()
        if raw and not raw.startswith("•"):  # a masked echo from the UI means "unchanged"
            if len(raw) < 4:
                raise HTTPException(422, "ID number looks too short")
            if raw != decrypt(profile.id_document_number):
                profile.id_document_number = encrypt(raw)
                id_changed = True
    if "id_document_type" in changes and (changes["id_document_type"] or None) != profile.id_document_type:
        id_changed = True
    for field, value in changes.items():
        if value is not None or field in ("bio",):
            setattr(profile, field, value)

    # (re)submitting ID details sends the profile back to the admin review queue
    if id_changed and profile.verification_status != "pending":
        profile.verification_status = "pending"
        profile.verification_note = None
    db.commit()
    db.refresh(profile)
    return tech_self(profile)


@router.patch("/me/availability", response_model=TechnicianSelf)
def set_availability(
    data: AvailabilityUpdate,
    user: User = Depends(require_roles("technician")),
    db: Session = Depends(get_db),
):
    profile = _own_profile(db, user)
    profile.is_available = data.is_available
    db.commit()
    db.refresh(profile)
    return tech_self(profile)


@router.get("/saved", response_model=list[TechnicianPublic])
def saved_technicians(user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(TechnicianProfile)
        .join(SavedTechnician, SavedTechnician.technician_id == TechnicianProfile.id)
        .where(SavedTechnician.customer_id == user.id)
        .order_by(SavedTechnician.created_at.desc())
    ).all()
    return [tech_public(t) for t in rows]


@router.post("/{technician_id}/save", status_code=status.HTTP_201_CREATED)
def save_technician(technician_id: int, user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    tech = db.get(TechnicianProfile, technician_id)
    if tech is None or tech.verification_status != "verified":
        raise HTTPException(404, "Technician not found")
    exists = db.scalar(select(SavedTechnician).where(
        SavedTechnician.customer_id == user.id, SavedTechnician.technician_id == technician_id))
    if exists is None:
        db.add(SavedTechnician(customer_id=user.id, technician_id=technician_id))
        db.commit()
    return {"saved": True}


@router.delete("/{technician_id}/save")
def unsave_technician(technician_id: int, user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    row = db.scalar(select(SavedTechnician).where(
        SavedTechnician.customer_id == user.id, SavedTechnician.technician_id == technician_id))
    if row is not None:
        db.delete(row)
        db.commit()
    return {"saved": False}


@router.get("/{technician_id}", response_model=TechnicianDetail)
def technician_detail(technician_id: int, db: Session = Depends(get_db), viewer: Optional[User] = Depends(get_optional_user)):
    tech = db.get(TechnicianProfile, technician_id)
    can_see_unverified = viewer is not None and (viewer.role == "admin" or viewer.id == getattr(tech, "user_id", None))
    if tech is None or (tech.verification_status != "verified" and not can_see_unverified):
        raise HTTPException(404, "Technician not found")
    reviews = db.scalars(
        select(Review).options(selectinload(Review.customer))
        .where(Review.technician_id == tech.id).order_by(Review.created_at.desc())
    ).all()
    is_saved = False
    if viewer is not None and viewer.role == "customer":
        is_saved = db.scalar(select(SavedTechnician.id).where(
            SavedTechnician.customer_id == viewer.id, SavedTechnician.technician_id == tech.id)) is not None
    return TechnicianDetail(**public_fields(tech), reviews=[review_out(r) for r in reviews], is_saved=is_saved)
