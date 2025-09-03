import uuid

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from open_prices.users.utils import get_session


def create_token(user_id: str) -> str:
    return f"{user_id}__U{str(uuid.uuid4())}"


def get_token_from_cookie(request: Request) -> str | None:
    return request.COOKIES.get(settings.SESSION_COOKIE_NAME)


def get_token_from_header(request: Request) -> str | None:
    """
    Expected format: "Bearer <user_id>__U<uuid>"
    """
    authorization = request.META.get("HTTP_AUTHORIZATION")
    if authorization and "bearer " in authorization.lower():
        return authorization.split(" ")[1]
    return None


def has_token_from_cookie_or_header(request: Request) -> bool:
    return (
        get_token_from_cookie(request) is not None
        or get_token_from_header(request) is not None
    )


def get_request_session(request: Request):
    try:
        # If a session cookie is present, use that instead of the header
        token_from_cookie = get_token_from_cookie(request)
        if token_from_cookie:
            return get_session(token=token_from_cookie)

        token_from_header = get_token_from_header(request)
        if token_from_header:
            return get_session(token=token_from_header)

    except:  # noqa
        pass

    return None


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request: Request):
        session = get_request_session(request)
        if session:
            return (session.user, None)
        # raise exceptions.AuthenticationFailed("Invalid authentication credentials")  # noqa
        return None


class MyCustomAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    https://drf-spectacular.readthedocs.io/en/latest/customization.html#specify-authentication-with-openapiauthenticationextension  # noqa
    """

    target_class = CustomAuthentication
    name = "CustomAuthentication"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization", token_prefix="Bearer"
        )
