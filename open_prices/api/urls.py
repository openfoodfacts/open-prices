from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from open_prices.api.views import StatusView

app_name = "api"

urlpatterns = [
    path("v1/auth", include("open_prices.api.auth.urls")),
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
