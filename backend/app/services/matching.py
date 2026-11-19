"""Smart technician matching: filter verified technicians by skill, then rank them.

Score (0-100):
  rating        40  (avg_rating / 5 * 40; unrated technicians get a neutral 20)
  location      30  (same city = 30; no city supplied = neutral 15; otherwise 0)
  availability  20  (currently available)
  experience    10  (1 point per year, capped at 10)
Ties are broken by lower base rate.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TechnicianProfile, User


def match_technicians(
    db: Session,
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    available_only: bool = False,
    limit: int = 30,
) -> list[tuple[TechnicianProfile, float, list[str]]]:
    stmt = (
        select(TechnicianProfile)
        .join(User, User.id == TechnicianProfile.user_id)
        .where(TechnicianProfile.verification_status == "verified", User.is_active.is_(True))
    )
    if category_id is not None:
        stmt = stmt.where(TechnicianProfile.categories.any(id=category_id))
    if available_only:
        stmt = stmt.where(TechnicianProfile.is_available.is_(True))

    wanted_city = (city or "").strip().lower()
    results = []
    for tech in db.scalars(stmt).all():
        reasons: list[str] = []
        if tech.review_count:
            rating_pts = tech.avg_rating / 5 * 40
            reasons.append(f"Rated {tech.avg_rating:.1f}/5 from {tech.review_count} reviews")
        else:
            rating_pts = 20
            reasons.append("New on ServiceFlow (no reviews yet)")
        if not wanted_city:
            city_pts = 15
        elif tech.city.strip().lower() == wanted_city:
            city_pts = 30
            reasons.append(f"Based in {tech.city}")
        else:
            city_pts = 0
            reasons.append(f"Located in {tech.city}, outside {city.strip()}")
        avail_pts = 20 if tech.is_available else 0
        reasons.append("Available now" if tech.is_available else "Currently unavailable")
        exp_pts = min(tech.experience_years, 10)
        if tech.experience_years:
            reasons.append(f"{tech.experience_years} yrs experience")
        results.append((tech, round(rating_pts + city_pts + avail_pts + exp_pts, 1), reasons))

    results.sort(key=lambda r: (-r[1], r[0].base_rate, r[0].id))
    return results[:limit]
