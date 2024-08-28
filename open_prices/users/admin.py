from django.contrib import admin

from open_prices.users.models import Session, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "is_moderator", "price_count", "created")
    list_filter = ("is_moderator",)
    search_fields = ("user_id",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created", "last_used")
    search_fields = ("token",)
