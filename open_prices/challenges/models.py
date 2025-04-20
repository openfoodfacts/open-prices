from django.contrib.postgres.fields import ArrayField
from django.core.validators import ValidationError
from django.db import models
from django.db.models import Case, Value, When
from django.utils import timezone

from open_prices.challenges import constants as challenge_constants
from open_prices.common import utils


class ChallengeQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def with_status(self):
        return self.annotate(
            status_annotated=Case(
                When(
                    is_published=False,
                    then=Value(challenge_constants.CHALLENGE_STATUS_DRAFT),
                ),
                When(
                    start_date__gt=timezone.now().date(),
                    then=Value(challenge_constants.CHALLENGE_STATUS_UPCOMING),
                ),
                When(
                    end_date__lt=timezone.now().date(),
                    then=Value(challenge_constants.CHALLENGE_STATUS_COMPLETED),
                ),
                default=Value(challenge_constants.CHALLENGE_STATUS_ONGOING),
                output_field=models.CharField(),
            )
        )


class Challenge(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    subtitle = models.CharField(max_length=200, blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    categories = ArrayField(base_field=models.CharField(), blank=True, default=list)
    example_proof_url = models.CharField(max_length=200, blank=True, null=True)

    is_published = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = ChallengeQuerySet.as_manager()

    class Meta:
        db_table = "challenges"
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

    def clean(self, *args, **kwargs):
        validation_errors = dict()
        # date rules
        if self.start_date is not None and self.end_date is not None:
            if str(self.start_date) > str(self.end_date):
                utils.add_validation_error(
                    validation_errors, "start_date", "Must be before end date"
                )
        # published rules
        if self.is_published:
            if self.title is None:
                utils.add_validation_error(
                    validation_errors, "title", "Must be set if challenge is published"
                )
            if self.start_date is None:
                utils.add_validation_error(
                    validation_errors,
                    "start_date",
                    "Must be set if challenge is published",
                )
            if self.end_date is None:
                utils.add_validation_error(
                    validation_errors,
                    "end_date",
                    "Must be set if challenge is published",
                )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def status(self) -> str:
        if not self.is_published:
            return challenge_constants.CHALLENGE_STATUS_DRAFT
        elif self.start_date is None or self.end_date is None:
            pass  # cannot happen (see full_clean validation)
        elif str(self.start_date) > str(timezone.now().date()):
            return challenge_constants.CHALLENGE_STATUS_UPCOMING
        elif str(self.end_date) < str(timezone.now().date()):
            return challenge_constants.CHALLENGE_STATUS_COMPLETED
        else:
            return challenge_constants.CHALLENGE_STATUS_ONGOING
