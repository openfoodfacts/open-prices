from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from open_prices.api.auth.views import LoginView, SessionView
from open_prices.api.challenges.views import ChallengeViewSet
from open_prices.api.locations.views import LocationViewSet
from open_prices.api.prices.views import PriceViewSet
from open_prices.api.products.views import ProductViewSet
from open_prices.api.proofs.views import PriceTagViewSet, ProofViewSet
from open_prices.api.stats.views import StatsView
from open_prices.api.users.views import UserViewSet
from open_prices.api.views import StatusView

app_name = "api"

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"v1/users", UserViewSet, basename="users")
router.register(r"v1/locations", LocationViewSet, basename="locations")
router.register(r"v1/products", ProductViewSet, basename="products")
router.register(r"v1/proofs", ProofViewSet, basename="proofs")
router.register(r"v1/prices", PriceViewSet, basename="prices")
router.register(r"v1/price-tags", PriceTagViewSet, basename="price-tags")
router.register(r"v1/challenges", ChallengeViewSet, basename="challenges")

urlpatterns = [
    # auth urls
    path("v1/auth", LoginView.as_view(), name="login"),
    path("v1/session", SessionView.as_view(), name="session"),
    # stats urls
    path("v1/stats", StatsView.as_view(), name="stats"),
    # health check
    path("v1/status", StatusView.as_view(), name="status"),
    # Swagger / OpenAPI documentation
    path("schema", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="swagger-ui",
    ),
    path("redoc", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

urlpatterns += router.urls
