import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_system: bool
    permission_codes: list[str]


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = None
    permission_codes: list[str] = []


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool


class CompanyUserOut(UserOut):
    role_id: uuid.UUID
    role_name: str


class UserInvite(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_id: uuid.UUID


class UserRoleUpdate(BaseModel):
    role_id: uuid.UUID


class PermissionOut(BaseModel):
    code: str
    description: str
