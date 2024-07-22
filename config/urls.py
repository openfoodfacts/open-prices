from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("open_prices.www.urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns += debug_toolbar_urls()
