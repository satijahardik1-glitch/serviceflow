from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    phone: Optional[str] = Field(default=None, max_length=30)
    city: Optional[str] = Field(default=None, max_length=100)
    role: Literal["customer", "technician"] = "customer"
    # technician-only fields
    category_ids: list[int] = []
    bio: Optional[str] = Field(default=None, max_length=2000)
    base_rate: float = Field(default=0, ge=0)
    experience_years: int = Field(default=0, ge=0, le=60)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Password must contain at least one letter and one number")
        return v

    @model_validator(mode="after")
    def technician_requirements(self):
        if self.role == "technician":
            if not self.city or not self.city.strip():
                raise ValueError("City is required for technicians")
            if not self.category_ids:
                raise ValueError("Select at least one service category")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
