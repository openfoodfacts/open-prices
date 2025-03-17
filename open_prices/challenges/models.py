from django.contrib.postgres.fields import ArrayField
from django.core.validators import ValidationError
from django.db import models
from django.utils import timezone

from open_prices.challenges import constants as challenge_constants
from open_prices.common import utils


class Challenge(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    subtitle = models.CharField(max_length=200, blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    categories = ArrayField(base_field=models.CharField(), blank=True, default=list)
    example_proof_url = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=challenge_constants.CHALLENGE_STATUS_CHOICES
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "challenges"
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

    def clean(self, *args, **kwargs):
        validation_errors = dict()
        # date rules
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                utils.add_validation_error(
                    validation_errors, "start_date", "Must be before end date"
                )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
