from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from open_prices.common import constants, utils
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants

from .proof import Proof


class PriceTag(models.Model):
    """A single price tag in a proof."""

    UPDATE_FIELDS = ["bounding_box", "status", "price_id"]
    CREATE_FIELDS = UPDATE_FIELDS + ["proof_id"]

    proof = models.ForeignKey(
        Proof,
        on_delete=models.CASCADE,
        related_name="price_tags",
        verbose_name="The proof this price tag belongs to",
    )
    price = models.ForeignKey(
        Price,
        on_delete=models.SET_NULL,
        related_name="price_tags",
        null=True,
        blank=True,
        verbose_name="The price linked to this tag",
    )
    created = models.DateTimeField(
        default=timezone.now, verbose_name="When the tag was created in DB"
    )
    updated = models.DateTimeField(
        auto_now=True, verbose_name="When the tag was last updated"
    )
    bounding_box = ArrayField(
        base_field=models.FloatField(),
        verbose_name="Coordinates of the bounding box, in the format [y_min, x_min, y_max, x_max]",
    )
    status = models.IntegerField(
        choices=constants.PRICE_TAG_STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name="The annotation status. Possible values are: "
        "- null: not annotated yet"
        "- 0 (the price tag was deleted by a user)"
        "- 1 (the price tag is linked to a price)"
        "- 2 (the price tag barcode or price cannot be read)"
        "- 3 (the object is not a price tag)",
    )
    model_version = models.CharField(
        max_length=30,
        verbose_name="The version of the object detector model that generated the prediction",
        blank=True,
        null=True,
    )
    created_by = models.CharField(
        max_length=100,
        verbose_name="The name of the user who created this price tag. This field is null if "
        "the tag was created by a model.",
        null=True,
        blank=True,
    )
    updated_by = models.CharField(
        max_length=100,
        verbose_name="The name of the user who last updated this price tag bounding boxes. "
        "If the price tag bounding boxes were never updated, this field is null.",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "price_tags"
        verbose_name = "Price Tag"
        verbose_name_plural = "Price Tags"

    def __str__(self):
        return f"{self.proof} - {self.status}"

    def clean(self, *args, **kwargs):
        validation_errors = dict()
        if self.bounding_box is not None:
            if len(self.bounding_box) != 4:
                utils.add_validation_error(
                    validation_errors,
                    "bounding_box",
                    "Bounding box should have 4 values.",
                )
            else:
                if not all(isinstance(value, float) for value in self.bounding_box):
                    utils.add_validation_error(
                        validation_errors,
                        "bounding_box",
                        "Bounding box values should be floats.",
                    )
                elif not all(value >= 0 and value <= 1 for value in self.bounding_box):
                    utils.add_validation_error(
                        validation_errors,
                        "bounding_box",
                        "Bounding box values should be between 0 and 1.",
                    )
                else:
                    y_min, x_min, y_max, x_max = self.bounding_box
                    if y_min >= y_max or x_min >= x_max:
                        utils.add_validation_error(
                            validation_errors,
                            "bounding_box",
                            "Bounding box values should be in the format [y_min, x_min, y_max, x_max].",
                        )

        # self.proof and self.price is fetched with select_related in the view
        # when the action is "create" or "update"
        # We therefore only check the validity of the relationship if the user
        # tries to update the price tag
        if self.proof:
            if self.proof.type != proof_constants.TYPE_PRICE_TAG:
                utils.add_validation_error(
                    validation_errors,
                    "proof",
                    "Proof should have type PRICE_TAG.",
                )

        if self.price:
            if self.proof and self.price.proof_id != self.proof.id:
                utils.add_validation_error(
                    validation_errors,
                    "price",
                    "Price should belong to the same proof.",
                )

            if self.status is None:
                self.status = constants.PriceTagStatus.linked_to_price.value
            elif self.status != constants.PriceTagStatus.linked_to_price.value:
                utils.add_validation_error(
                    validation_errors,
                    "status",
                    "Status should be `linked_to_price` when price_id is set.",
                )

        if bool(validation_errors):
            raise ValidationError(validation_errors)

        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
