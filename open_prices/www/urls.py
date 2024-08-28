from django.urls import path

from open_prices.www.views import HomeView

app_name = "www"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
