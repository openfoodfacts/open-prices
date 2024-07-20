from django.urls import path

from www.views import HomeView

app_name = "www"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
