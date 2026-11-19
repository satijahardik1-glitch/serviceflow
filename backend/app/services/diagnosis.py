"""Deterministic, rule-based problem diagnosis and price estimation.

Scoring: every rule of the chosen category is scored against the customer's text
(free-text description + selected symptom chips).
  * +5 when the rule's symptom chip was explicitly selected / appears verbatim
  * +2 per matched multi-word keyword, +1 per matched single-word keyword
  * rule.priority / 10 is added as a deterministic tie-breaker
The highest scoring rule wins; if nothing matches, the category's default rule is used.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DiagnosisRule, ServiceCategory
from app.schemas.service import DiagnosisOut


def _keywords(rule: DiagnosisRule) -> list[str]:
    return [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]


def diagnose(db: Session, category_id: int, description: str, symptoms: list[str]) -> DiagnosisOut:
    category = db.get(ServiceCategory, category_id)
    if category is None:
        raise LookupError("Service category not found")
    rules = db.scalars(select(DiagnosisRule).where(DiagnosisRule.category_id == category_id)).all()
    if not rules:
        raise LookupError("No diagnosis rules configured for this category")

    chips = {s.strip().lower() for s in symptoms if s.strip()}
    text = " ".join([description or "", *symptoms]).lower()

    best, best_score, best_hits = None, 0.0, []
    for rule in rules:
        if rule.is_default:
            continue
        hits = [k for k in _keywords(rule) if k in text]
        score = sum(2 if " " in k else 1 for k in hits)
        if rule.symptom.lower() in chips:
            score += 5
            hits = [rule.symptom.lower(), *[h for h in hits if h != rule.symptom.lower()]]
        if score == 0:
            continue
        score += rule.priority / 10
        if score > best_score:
            best, best_score, best_hits = rule, score, hits

    is_fallback = best is None
    if is_fallback:
        best = next((r for r in rules if r.is_default), rules[0])
        confidence = 0.3
    else:
        confidence = round(min(0.95, 0.45 + 0.1 * len(best_hits) + (0.2 if best.symptom.lower() in chips else 0)), 2)

    return DiagnosisOut(
        category_id=category.id, category_name=category.name, diagnosis=best.diagnosis,
        estimated_minutes=best.estimated_minutes, min_price=best.min_price, max_price=best.max_price,
        matched_keywords=best_hits[:6], confidence=confidence, is_fallback=is_fallback,
        symptom=None if is_fallback else best.symptom,
    )
