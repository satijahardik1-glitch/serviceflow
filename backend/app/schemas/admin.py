from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminMetrics(BaseModel):
    total_users: int
    customers: int
    technicians: int
    technicians_pending: int
    technicians_verified: int
    technicians_rejected: int
    total_bookings: int
    bookings_by_status: dict[str, int]
    completed_value_estimate: float
    average_platform_rating: float


class VerificationUpdate(BaseModel):
    status: Literal["pending", "verified", "rejected"]
    note: Optional[str] = Field(default=None, max_length=1000)


class UserStatusUpdate(BaseModel):
    is_active: bool


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="🛠️", max_length=16)


class RuleIn(BaseModel):
    symptom: str = Field(min_length=2, max_length=120)
    keywords: str = Field(default="", max_length=2000)
    diagnosis: str = Field(min_length=3, max_length=255)
    min_price: float = Field(ge=0)
    max_price: float = Field(ge=0)
    estimated_minutes: int = Field(ge=5, le=1440)
    priority: int = Field(default=0, ge=0, le=100)
    is_default: bool = False

    @model_validator(mode="after")
    def normalise(self):
        if self.max_price < self.min_price:
            raise ValueError("Maximum price must be at least the minimum price")
        seen, cleaned = set(), []
        for k in self.keywords.split(","):
            k = k.strip().lower()
            if k and k not in seen:
                seen.add(k)
                cleaned.append(k)
        self.keywords = ",".join(cleaned)
        return self


class RuleCreate(RuleIn):
    category_id: int


class RuleOut(RuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
