from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    icon: str


class DiagnoseRequest(BaseModel):
    category_id: int
    description: str = Field(default="", max_length=2000)
    symptoms: list[str] = []


class DiagnosisOut(BaseModel):
    category_id: int
    category_name: str
    diagnosis: str
    estimated_minutes: int
    min_price: float
    max_price: float
    matched_keywords: list[str]
    confidence: float
    is_fallback: bool
    symptom: Optional[str] = None
