from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from open_prices.api.users.views import UserViewSet
from open_prices.api.views import StatusView

app_name = "api"

router = routers.DefaultRouter()
router.register(r"v1/users", UserViewSet, basename="users")

urlpatterns = [
    path("v1/auth/", include("open_prices.api.auth.urls")),
    path("v1/status", StatusView.as_view(), name="status"),
    # Swagger / OpenAPI documentation
    path("v1/schema", SpectacularAPIView.as_view(), name="schema"),
    path(
        "v1/docs",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="swagger-ui",
    ),
    path("v1/redoc", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

urlpatterns += router.urls
