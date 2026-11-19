from fastapi import Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class PageParams:
    def __init__(self, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        self.limit = limit
        self.offset = offset


def paginate(db: Session, stmt, response: Response, page: PageParams):
    """Apply limit/offset and expose the total row count in the X-Total-Count header."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    response.headers["X-Total-Count"] = str(total or 0)
    return db.scalars(stmt.limit(page.limit).offset(page.offset)).all()
