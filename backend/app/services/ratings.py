from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Review, TechnicianProfile


def recompute_rating(db: Session, technician_id: int) -> None:
    avg, count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.technician_id == technician_id)
    ).one()
    tech = db.get(TechnicianProfile, technician_id)
    tech.avg_rating = round(float(avg), 2) if avg is not None else 0
    tech.review_count = int(count)
