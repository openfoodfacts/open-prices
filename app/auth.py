from typing import Annotated, Any, Optional, cast

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from app import crud
from app.db import get_db
from app.models import User


# This class is derived from FastAPI's OAuth2PasswordBearer class,
# but adds support for cookie sessions.
class OAuth2PasswordBearerOrAuthCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str | None = None,
        scopes: dict[str, str] | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password=cast(Any, {"tokenUrl": tokenUrl, "scopes": scopes})
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        session_cookie = request.cookies.get("opsession")
        scheme, param = get_authorization_scheme_param(authorization)

        # If a session cookie is present, use that instead of the
        # Authorization header.
        if session_cookie:
            return session_cookie

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


# Authentication helpers
# ------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearerOrAuthCookie(tokenUrl="auth")
# Version of oauth2_scheme that does not raise an error if the token is
# invalid or missing
oauth2_scheme_no_error = OAuth2PasswordBearerOrAuthCookie(
    tokenUrl="auth", auto_error=False
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    """Get the current user if authenticated.

    This function is used as a dependency in endpoints that require
    authentication. It raises an HTTPException if the user is not
    authenticated.

    :param token: the authentication token
    :param db: the database session
    :raises HTTPException: if the user is not authenticated
    :return: the current user
    """
    if token and "__U" in token:
        session = crud.get_session_by_token(db, token=token)
        if session:
            return crud.update_session_last_used_field(db, session=session).user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
