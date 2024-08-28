from django.urls import path

from open_prices.api.auth.views import LoginView, SessionView

app_name = "auth"

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("session", SessionView.as_view(), name="session"),
]
