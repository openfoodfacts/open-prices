from django.urls import path

from open_prices.api.auth.views import LoginView

app_name = "auth"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
]
