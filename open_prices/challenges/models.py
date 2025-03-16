from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from open_prices.challenges import constants as challenge_constants


class Challenge(models.Model):
    challenge_id = models.CharField(primary_key=True)
    state = models.CharField(
        max_length=20, choices=challenge_constants.CHALLENGE_STATE_CHOICES
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    categories = ArrayField(base_field=models.CharField(), blank=True, default=list)
    example_proof_url = models.CharField(max_length=200, blank=True, null=True)

    created = models.DateTimeField(
        default=timezone.now, verbose_name="When the prediction was created in DB"
    )
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "challenges"
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"
