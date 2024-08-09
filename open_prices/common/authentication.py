import uuid

from django.conf import settings
from rest_framework import authentication
from rest_framework.request import Request

from open_prices.users.utils import get_session


def create_token(user_id: str) -> str:
    return f"{user_id}__U{str(uuid.uuid4())}"


def get_authorization_token(authorization: str) -> str:
    return authorization.split(" ")[1]


def get_request_session(request: Request):
    authorization = request.META.get("HTTP_AUTHORIZATION")  # "Bearer <token>"
    session_cookie = request.COOKIES.get(settings.SESSION_COOKIE_NAME)

    try:
        # If a session cookie is present, use that instead of the
        # Authorization header
        if session_cookie:
            return get_session(token=session_cookie)

        if authorization and "__U" in authorization:
            return get_session(token=get_authorization_token(authorization))
    except:  # noqa
        pass

    return None


class CustomAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request):
        session = get_request_session(request)
        if session:
            return (session.user, None)
        # raise exceptions.AuthenticationFailed("Invalid authentication credentials")  # noqa
        return None
