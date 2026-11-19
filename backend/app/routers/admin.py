import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.pagination import PageParams, paginate
from app.db.session import get_db
from app.models import Booking, DiagnosisRule, ServiceCategory, TechnicianProfile, User, technician_categories
from app.routers.bookings import load_options
from app.schemas.admin import (
    AdminMetrics, CategoryCreate, RuleCreate, RuleIn, RuleOut, UserStatusUpdate, VerificationUpdate,
)
from app.schemas.booking import BookingOut, booking_out
from app.schemas.service import CategoryOut
from app.schemas.technician import TechnicianSelf, tech_self
from app.schemas.user import UserOut

logger = logging.getLogger("serviceflow.admin")
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])


@router.get("/metrics", response_model=AdminMetrics)
def metrics(db: Session = Depends(get_db)):
    role_counts = dict(db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all())
    ver_counts = dict(db.execute(
        select(TechnicianProfile.verification_status, func.count(TechnicianProfile.id))
        .group_by(TechnicianProfile.verification_status)).all())
    booking_counts = dict(db.execute(select(Booking.status, func.count(Booking.id)).group_by(Booking.status)).all())
    value = db.scalar(select(func.coalesce(func.sum((Booking.estimated_min_price + Booking.estimated_max_price) / 2), 0))
                      .where(Booking.status == "completed"))
    avg_rating = db.scalar(select(func.avg(TechnicianProfile.avg_rating)).where(TechnicianProfile.review_count > 0))
    return AdminMetrics(
        total_users=sum(role_counts.values()), customers=role_counts.get("customer", 0),
        technicians=role_counts.get("technician", 0),
        technicians_pending=ver_counts.get("pending", 0), technicians_verified=ver_counts.get("verified", 0),
        technicians_rejected=ver_counts.get("rejected", 0),
        total_bookings=sum(booking_counts.values()), bookings_by_status=booking_counts,
        completed_value_estimate=round(float(value or 0), 2),
        average_platform_rating=round(float(avg_rating or 0), 2),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(response: Response, role: Optional[str] = None, page: PageParams = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
    if role:
        stmt = stmt.where(User.role == role)
    return paginate(db, stmt, response, page)


@router.patch("/users/{user_id}/status", response_model=UserOut)
def set_user_status(user_id: int, data: UserStatusUpdate, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    if target.role == "admin":
        raise HTTPException(400, "Admin accounts cannot be deactivated here")
    target.is_active = data.is_active
    db.commit()
    db.refresh(target)
    logger.info("admin=%s set user=%s active=%s", admin.id, target.id, data.is_active)
    return target


@router.get("/technicians", response_model=list[TechnicianSelf])
def list_technicians(
    response: Response, status: Optional[str] = None, page: PageParams = Depends(),
    admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db),
):
    stmt = select(TechnicianProfile).order_by(TechnicianProfile.id.desc())
    if status:
        stmt = stmt.where(TechnicianProfile.verification_status == status)
    rows = paginate(db, stmt, response, page)
    logger.info("admin=%s viewed ID details of %d technicians", admin.id, len(rows))  # audit trail
    return [tech_self(t, reveal=True) for t in rows]


@router.patch("/technicians/{technician_id}/verification", response_model=TechnicianSelf)
def review_verification(technician_id: int, data: VerificationUpdate, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    tech = db.get(TechnicianProfile, technician_id)
    if tech is None:
        raise HTTPException(404, "Technician not found")
    if data.status == "verified" and not (tech.id_document_type and tech.id_document_number):
        raise HTTPException(409, "Technician has not submitted ID details yet")
    if data.status == "rejected" and not (data.note or "").strip():
        raise HTTPException(422, "Please add a note explaining the rejection")
    tech.verification_status = data.status
    tech.verification_note = (data.note or "").strip() or None
    db.commit()
    db.refresh(tech)
    logger.info("admin=%s set technician=%s verification=%s", admin.id, tech.id, data.status)
    return tech_self(tech, reveal=True)


@router.get("/bookings", response_model=list[BookingOut])
def all_bookings(response: Response, status: Optional[str] = None, page: PageParams = Depends(), db: Session = Depends(get_db)):
    stmt = select(Booking).options(*load_options()).order_by(Booking.created_at.desc(), Booking.id.desc())
    if status:
        stmt = stmt.where(Booking.status == status)
    return [booking_out(b) for b in paginate(db, stmt, response, page)]


# ---------------------------------------------------------------- service categories & diagnosis rules
def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    name, slug = data.name.strip(), _slugify(data.name)
    if not slug:
        raise HTTPException(422, "Category name must contain letters or numbers")
    if db.scalar(select(ServiceCategory.id).where(or_(ServiceCategory.name == name, ServiceCategory.slug == slug))):
        raise HTTPException(409, "A category with this name already exists")
    cat = ServiceCategory(name=name, slug=slug, description=data.description.strip(), icon=data.icon or "🛠️")
    db.add(cat)
    db.flush()
    # every category gets a fallback rule so diagnosis always returns something
    db.add(DiagnosisRule(
        category_id=cat.id, symptom=f"Other {name} issue", keywords="", is_default=True,
        diagnosis=f"General {name.lower()} fault - needs on-site inspection",
        min_price=300, max_price=1000, estimated_minutes=60, priority=0))
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.get(ServiceCategory, category_id)
    if cat is None:
        raise HTTPException(404, "Category not found")
    if db.scalar(select(func.count(Booking.id)).where(Booking.category_id == category_id)):
        raise HTTPException(409, "This category has bookings and cannot be deleted")
    if db.scalar(select(func.count()).select_from(technician_categories).where(technician_categories.c.category_id == category_id)):
        raise HTTPException(409, "Technicians still offer this category and it cannot be deleted")
    db.delete(cat)
    db.commit()
    return Response(status_code=204)


@router.get("/rules", response_model=list[RuleOut])
def list_rules(category_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(DiagnosisRule).where(DiagnosisRule.category_id == category_id)
                      .order_by(DiagnosisRule.is_default, DiagnosisRule.priority.desc(), DiagnosisRule.id)).all()


def _make_only_default(db: Session, category_id: int, keep_id: int) -> None:
    db.execute(update(DiagnosisRule).where(DiagnosisRule.category_id == category_id, DiagnosisRule.id != keep_id)
               .values(is_default=False))


@router.post("/rules", response_model=RuleOut, status_code=201)
def create_rule(data: RuleCreate, db: Session = Depends(get_db)):
    if db.get(ServiceCategory, data.category_id) is None:
        raise HTTPException(404, "Category not found")
    if not data.is_default and not data.keywords:
        raise HTTPException(422, "Add at least one keyword (only the fallback rule may have none)")
    rule = DiagnosisRule(**data.model_dump())
    db.add(rule)
    db.flush()
    if rule.is_default:
        _make_only_default(db, rule.category_id, rule.id)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, data: RuleIn, db: Session = Depends(get_db)):
    rule = db.get(DiagnosisRule, rule_id)
    if rule is None:
        raise HTTPException(404, "Rule not found")
    if not data.is_default and not data.keywords:
        raise HTTPException(422, "Add at least one keyword (only the fallback rule may have none)")
    if rule.is_default and not data.is_default:
        raise HTTPException(409, "Mark another rule as the fallback instead of unsetting this one")
    for field, value in data.model_dump().items():
        setattr(rule, field, value)
    if rule.is_default:
        _make_only_default(db, rule.category_id, rule.id)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(DiagnosisRule, rule_id)
    if rule is None:
        raise HTTPException(404, "Rule not found")
    if rule.is_default:
        raise HTTPException(409, "The fallback rule cannot be deleted - mark another rule as fallback first")
    db.delete(rule)
    db.commit()
    return Response(status_code=204)
