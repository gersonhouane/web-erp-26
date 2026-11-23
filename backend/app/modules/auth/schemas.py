import uuid

from pydantic import BaseModel, EmailStr, Field

from app.modules.core.schemas import CompanyCreate


class SignupIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    company: CompanyCreate
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str | None = None


class SwitchCompanyIn(BaseModel):
    company_id: uuid.UUID


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    company_id: uuid.UUID | None


class CompanyBrief(BaseModel):
    id: uuid.UUID
    name: str
    role: str


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    tenant_id: uuid.UUID
    company_id: uuid.UUID | None
    companies: list[CompanyBrief]
    permissions: list[str]
