import time

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from open_prices.api.auth.serializers import (
    LoginSerializer,
    SessionFullSerializer,
    SessionResponseSerializer,
)
from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.common.authentication import (
    CustomAuthentication,
    create_token,
    get_request_session,
)
from open_prices.users.utils import get_or_create_session


class LoginView(APIView):
    serializer_class = LoginSerializer
    parser_classes = [FormParser, MultiPartParser]

    @extend_schema(responses=SessionResponseSerializer, tags=["auth"])
    def post(self, request: Request) -> Response:
        """
        Authentication: provide username/password
        and get a bearer token in return.

        - **username**: Open Food Facts user_id (not email)
        - **password**: user password (clear text, but HTTPS encrypted)

        A **token** is returned. If the **set_cookie** parameter is set to 1,
        the token is also set as a cookie named "session" in the response.

        To authenticate, you can either:
        - use the **Authorization** header with the **Bearer** scheme,
        e.g.: "Authorization: bearer token"
        - use the **session** cookie, e.g.: "Cookie: session=token"
        """
        if not settings.OAUTH2_SERVER_URL:
            return Response(
                {"detail": "OAUTH2_SERVER_URL environment variable missing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # By specifying body=1, information about the user is returned in the
        # response, including the user_id
        response = common_openfoodfacts.authenticate(
            username=request.POST.get("username"), password=request.POST.get("password")
        )
        if response.status_code == 200:
            # form_data.username can be the user_id or the email, so we need to
            # fetch the user_id from the response
            # We also need to lowercase the user_id as it's case-insensitive
            user_id = response.json()["user_id"].lower().strip()
            is_moderator = response.json()["user"]["moderator"] == 1
            token = create_token(user_id)
            get_or_create_session(
                user_id=user_id, token=token, is_moderator=is_moderator
            )
            # set the cookie if requested
            response = Response({"access_token": token, "token_type": "bearer"})
            if request.GET.get("set_cookie") == "1":
                # Don't add httponly=True or secure=True as it's still in
                # development phase, but it should be added once the front-end
                # is ready
                response.set_cookie(settings.SESSION_COOKIE_NAME, token)
            return response
        elif response.status_code == 403:
            time.sleep(2)  # prevents brute-force
            return Response(
                {"detail": "Invalid authentication credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Response(
            {"detail": "Server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class SessionView(APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SessionFullSerializer

    @extend_schema(tags=["auth"])
    def get(self, request: Request) -> Response:
        session = get_request_session(request)
        return Response(
            {
                "user_id": session.user.user_id,
                "token": session.token,
                "created": session.created,
                "last_used": session.last_used,
            }
        )

    @extend_schema(tags=["auth"])
    def delete(self, request: Request) -> Response:
        session = get_request_session(request)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
