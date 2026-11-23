import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_nuit(value: str | None, country_code: str = "MZ") -> str | None:
    if value is None or value == "":
        return None
    value = value.strip()
    if country_code == "MZ" and not re.fullmatch(r"\d{9}", value):
        raise ValueError("O NUIT deve ter 9 dígitos.")
    return value


class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    nuit: str | None = None
    country_code: str = Field(default="MZ", min_length=2, max_length=2)
    base_currency: str = Field(default="MZN", min_length=3, max_length=3)
    address_street: str | None = None
    address_neighbourhood: str | None = None
    address_number: str | None = None
    city: str | None = None
    province: str | None = None
    fiscal_area: str | None = None

    @field_validator("country_code", "base_currency")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("nuit")
    @classmethod
    def _nuit(cls, v: str | None, info) -> str | None:
        return validate_nuit(v, (info.data.get("country_code") or "MZ").upper())


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    nuit: str | None = None
    address_street: str | None = None
    address_neighbourhood: str | None = None
    address_number: str | None = None
    city: str | None = None
    province: str | None = None
    fiscal_area: str | None = None


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    address: str | None = None


class BranchOut(BranchCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity: str
    entity_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime
