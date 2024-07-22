from django.db import models
from django.utils import timezone


class User(models.Model):
    user_id = models.CharField(primary_key=True)

    is_moderator = models.BooleanField(default=False)

    price_count = models.PositiveIntegerField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    # updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"


class Session(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.DO_NOTHING, related_name="sessions")
    token = models.CharField(unique=True)

    created = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "sessions"
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
