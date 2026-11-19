from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.ratelimit import limiter, rate_limit, too_many
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import ServiceCategory, TechnicianProfile, User
from app.schemas.user import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user.id, user.role), user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("register", 10, 3600))])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    categories = []
    if data.role == "technician":
        ids = set(data.category_ids)
        categories = list(db.scalars(select(ServiceCategory).where(ServiceCategory.id.in_(ids))).all())
        if len(categories) != len(ids):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "One or more service categories are invalid")

    user = User(
        name=data.name.strip(), email=email, hashed_password=hash_password(data.password),
        role=data.role, phone=data.phone, city=data.city.strip() if data.city else None,
    )
    db.add(user)
    db.flush()
    if data.role == "technician":
        db.add(TechnicianProfile(
            user_id=user.id, bio=data.bio, city=data.city.strip(), base_rate=data.base_rate,
            experience_years=data.experience_years, categories=categories, verification_status="pending",
        ))
    db.commit()
    db.refresh(user)
    return _token_response(user)


MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("login", 30, 60))])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email = data.email.lower()
    fail_key = f"login-fail:{email}"
    if settings.RATE_LIMIT_ENABLED and limiter.count(fail_key, LOCKOUT_SECONDS) >= MAX_FAILED_LOGINS:
        raise too_many(LOCKOUT_SECONDS)  # temporary lockout after repeated failures
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(data.password, user.hashed_password):
        limiter.add(fail_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")
    limiter.clear(fail_key)
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
