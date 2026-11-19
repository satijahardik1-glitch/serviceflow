"""JWT authentication dependencies and role-based access control guards."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _user_from_credentials(creds: Optional[HTTPAuthorizationCredentials], db: Session) -> Optional[User]:
    if creds is None:
        return None
    try:
        user_id = int(decode_access_token(creds.credentials)["sub"])
    except (JWTError, KeyError, ValueError):
        raise _credentials_error()
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _credentials_error()
    return user


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_credentials(creds, db)
    if user is None:
        raise _credentials_error()
    return user


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _user_from_credentials(creds, db)


def require_roles(*roles: str):
    """RBAC guard factory: `Depends(require_roles("admin"))`."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to perform this action")
        return user

    return checker
