from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user, get_db
from app.core.errors import Unauthorized
from app.modules.auth import service
from app.modules.auth.schemas import (
    CompanyBrief,
    LoginIn,
    MeOut,
    RefreshIn,
    SignupIn,
    SwitchCompanyIn,
    TokenOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "weberp_refresh"


def _set_cookie(response: Response, tokens: TokenOut) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        path="/api/v1/auth",
    )


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(data: SignupIn, request: Request, response: Response, db: Session = Depends(get_db)):
    """Regista uma nova organização (cliente), a primeira empresa e o administrador."""
    tokens = service.signup(db, data, _ip(request))
    _set_cookie(response, tokens)
    return tokens


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    tokens = service.login(db, data.email, data.password, _ip(request))
    _set_cookie(response, tokens)
    return tokens


@router.post("/refresh", response_model=TokenOut)
def refresh(
    response: Response,
    data: RefreshIn | None = None,
    cookie_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: Session = Depends(get_db),
):
    """Aceita o refresh token no corpo (NextAuth, app Flutter) ou no cookie (browser)."""
    raw = (data.refresh_token if data else None) or cookie_token
    if not raw:
        raise Unauthorized("INVALID_REFRESH_TOKEN", "Sessão expirada. Entre de novo.")
    tokens = service.refresh(db, raw)
    _set_cookie(response, tokens)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    data: RefreshIn | None = None,
    cookie_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: Session = Depends(get_db),
):
    raw = (data.refresh_token if data else None) or cookie_token
    if raw:
        service.logout(db, raw)
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.post("/switch-company", response_model=TokenOut)
def switch_company(
    data: SwitchCompanyIn,
    response: Response,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tokens = service.switch_company(db, current.user, data.company_id)
    _set_cookie(response, tokens)
    return tokens


@router.get("/me", response_model=MeOut)
def me(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    companies = service.user_companies(db, current.user)
    return MeOut(
        id=current.user.id,
        name=current.user.name,
        email=current.user.email,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        companies=[CompanyBrief(id=c.id, name=c.name, role=r) for c, r in companies],
        permissions=sorted(current.permissions),
    )
