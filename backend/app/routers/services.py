from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ratelimit import rate_limit
from app.db.session import get_db
from app.models import DiagnosisRule, ServiceCategory
from app.schemas.service import CategoryOut, DiagnoseRequest, DiagnosisOut
from app.services.diagnosis import diagnose

router = APIRouter(prefix="/services", tags=["services & diagnosis"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(ServiceCategory).order_by(ServiceCategory.id)).all()


@router.get("/symptoms", response_model=list[str])
def list_symptoms(category_id: int, db: Session = Depends(get_db)):
    """Common symptoms (selectable chips) for a category."""
    rows = db.scalars(
        select(DiagnosisRule.symptom)
        .where(DiagnosisRule.category_id == category_id, DiagnosisRule.is_default.is_(False))
        .order_by(DiagnosisRule.priority.desc(), DiagnosisRule.id)
    ).all()
    return list(rows)


@router.post("/diagnose", response_model=DiagnosisOut, dependencies=[Depends(rate_limit("diagnose", 60, 60))])
def diagnose_problem(data: DiagnoseRequest, db: Session = Depends(get_db)):
    if not data.description.strip() and not data.symptoms:
        raise HTTPException(422, "Describe the problem or select at least one symptom")
    try:
        return diagnose(db, data.category_id, data.description, data.symptoms)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
