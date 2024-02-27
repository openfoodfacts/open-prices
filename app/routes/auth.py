import time
import uuid
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import oauth2_scheme
from app.config import settings
from app.db import get_db
from app.models import Session as SessionModel

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
session_router = APIRouter(prefix="/session", tags=["Auth"])


def create_token(user_id: str):
    return f"{user_id}__U{str(uuid.uuid4())}"


def get_current_session(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> SessionModel:
    """Get the current user session, if authenticated.

    This function is used as a dependency in endpoints that require
    authentication. It raises an HTTPException if the user is not
    authenticated.

    :param token: the authentication token
    :param db: the database session
    :raises HTTPException: if the user is not authenticated
    :return: the current user session
    """
    if token and "__U" in token:
        session = crud.get_session_by_token(db, token=token)
        if session:
            return crud.update_session_last_used_field(db, session=session)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@auth_router.post("", tags=["Auth"])
def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    set_cookie: Annotated[
        bool,
        Query(
            description="if set to 1, the token is also set as a cookie "
            "named 'session' in the response. This parameter must be passed "
            "as a query parameter, e.g.: /auth?set_cookie=1"
        ),
    ] = False,
    db: Session = Depends(get_db),
):
    """
    Authentication: provide username/password and get a bearer token in return.

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    A **token** is returned. If the **set_cookie** parameter is set to 1,
    the token is also set as a cookie named "session" in the response.

    To authenticate, you can either:
    - use the **Authorization** header with the **Bearer** scheme,
      e.g.: "Authorization: bearer token"
    - use the **session** cookie, e.g.: "Cookie: session=token"
    """
    if "oauth2_server_url" not in settings.model_dump():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAUTH2_SERVER_URL environment variable missing",
        )

    # By specifying body=1, information about the user is returned in the
    # response, including the user_id
    data = {"user_id": form_data.username, "password": form_data.password, "body": 1}
    r = requests.post(f"{settings.oauth2_server_url}", data=data)  # type: ignore
    if r.status_code == 200:
        # form_data.username can be the user_id or the email, so we need to
        # fetch the user_id from the response
        # We also need to lowercase the user_id as it's case-insensitive
        user_id = r.json()["user_id"].lower().strip()
        token = create_token(user_id)
        session, *_ = crud.create_session(db, user_id=user_id, token=token)
        session = crud.update_session_last_used_field(db, session=session)
        # set the cookie if requested
        if set_cookie:
            # Don't add httponly=True or secure=True as it's still in
            # development phase, but it should be added once the front-end
            # is ready
            response.set_cookie(key="opsession", value=token)
        return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        time.sleep(2)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
    )


@session_router.get("", response_model=schemas.SessionBase, tags=["Auth"])
def get_user_session(
    current_session: SessionModel = Depends(get_current_session),
):
    """Return information about the current user session."""
    return current_session


@session_router.delete("", tags=["Auth"])
def delete_user_session(
    current_session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Delete the current user session.

    If the provided session token or cookie is invalid, a HTTP 401 response
    is returned.
    """
    crud.delete_session(db, current_session.id)
    return {"status": "ok"}
