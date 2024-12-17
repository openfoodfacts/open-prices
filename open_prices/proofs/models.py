import decimal

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task

from open_prices.common import constants, utils
from open_prices.locations import constants as location_constants
from open_prices.proofs import constants as proof_constants


class ProofQuerySet(models.QuerySet):
    def has_type_price_tag(self):
        return self.filter(type=proof_constants.TYPE_PRICE_TAG)

    def has_type_receipt(self):
        return self.filter(type=proof_constants.TYPE_RECEIPT)

    def has_type_gdpr_request(self):
        return self.filter(type=proof_constants.TYPE_GDPR_REQUEST)

    def has_type_shop_import(self):
        return self.filter(type=proof_constants.TYPE_SHOP_IMPORT)

    def has_type_single_shop(self):
        return self.filter(type__in=proof_constants.TYPE_SINGLE_SHOP_LIST)

    def has_type_shopping_session(self):
        return self.filter(type__in=proof_constants.TYPE_SHOPPING_SESSION_LIST)

    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_stats(self):
        return self.annotate(price_count_annotated=Count("prices", distinct=True))


class Proof(models.Model):
    FILE_FIELDS = ["file_path", "mimetype", "image_thumb_path"]
    UPDATE_FIELDS = [
        "location_osm_id",
        "location_osm_type",
        "type",
        "currency",
        "date",
        "receipt_price_count",
        "receipt_price_total",
    ]
    CREATE_FIELDS = UPDATE_FIELDS + [
        "location_id",  # extra field (optional)
    ]
    FIX_PRICE_FIELDS = ["location", "date", "currency"]
    DUPLICATE_LOCATION_FIELDS = [
        "location_osm_id",
        "location_osm_type",
    ]

    file_path = models.CharField(blank=True, null=True)
    mimetype = models.CharField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=proof_constants.TYPE_CHOICES)

    image_thumb_path = models.CharField(blank=True, null=True)

    location_osm_id = models.PositiveBigIntegerField(blank=True, null=True)
    location_osm_type = models.CharField(
        max_length=10,
        choices=location_constants.OSM_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="proofs",
    )
    date = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=3, choices=constants.CURRENCY_CHOICES, blank=True, null=True
    )

    receipt_price_count = models.PositiveIntegerField(
        verbose_name="Receipt's number of prices (user input)", blank=True, null=True
    )
    receipt_price_total = models.DecimalField(
        verbose_name="Receipt's total amount (user input)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(ProofQuerySet)()

    class Meta:
        # managed = False
        db_table = "proofs"
        verbose_name = "Proof"
        verbose_name_plural = "Proofs"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # proof rules
        # - date should have the right format & not be in the future
        if self.date:
            if type(self.date) is str:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "date",
                    "Parsing error. Expected format: YYYY-MM-DD",
                )
            elif self.date > timezone.now().date():
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "date",
                    "Should not be in the future",
                )
        # location rules
        # - allow passing a location_id
        # - location_osm_id should be set if location_osm_type is set
        # - location_osm_type should be set if location_osm_id is set
        # - some location fields should match the proof fields (on create)
        if self.location_id:
            location = None
            from open_prices.locations.models import Location

            try:
                location = Location.objects.get(id=self.location_id)
            except Location.DoesNotExist:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "location",
                    "Location not found",
                )

            if location:
                if location.type == location_constants.TYPE_ONLINE:
                    if self.location_osm_id:
                        validation_errors = utils.add_validation_error(
                            validation_errors,
                            "location_osm_id",
                            "Can only be set if location type is OSM",
                        )
                    if self.location_osm_type:
                        validation_errors = utils.add_validation_error(
                            validation_errors,
                            "location_osm_type",
                            "Can only be set if location type is OSM",
                        )
                elif location.type == location_constants.TYPE_OSM:
                    if not self.id:  # skip these checks on update
                        for LOCATION_FIELD in Proof.DUPLICATE_LOCATION_FIELDS:
                            location_field_value = getattr(
                                self.location, LOCATION_FIELD.replace("location_", "")
                            )
                            if location_field_value:
                                proof_field_value = getattr(self, LOCATION_FIELD)
                                if str(location_field_value) != str(proof_field_value):
                                    validation_errors = utils.add_validation_error(
                                        validation_errors,
                                        "location",
                                        f"Location {LOCATION_FIELD} ({location_field_value}) does not match the proof {LOCATION_FIELD} ({proof_field_value})",
                                    )
        else:
            if self.location_osm_id:
                if not self.location_osm_type:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "location_osm_type",
                        "Should be set if `location_osm_id` is filled",
                    )
            if self.location_osm_type:
                if not self.location_osm_id:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "location_osm_id",
                        "Should be set if `location_osm_type` is filled",
                    )
                elif self.location_osm_id in [True, "true", "false", "none", "null"]:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "location_osm_id",
                        "Should not be a boolean or an invalid string",
                    )
            # receipt-specific rules
            if not self.type == proof_constants.TYPE_RECEIPT:
                if self.receipt_price_count is not None:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "receipt_price_count",
                        "Can only be set if type RECEIPT",
                    )
                if self.receipt_price_total is not None:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "receipt_price_total",
                        "Can only be set if type RECEIPT",
                    )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def set_location(self):
        if self.location_osm_id and self.location_osm_type:
            from open_prices.locations import constants as location_constants
            from open_prices.locations.models import Location

            location, created = Location.objects.get_or_create(
                type=location_constants.TYPE_OSM,
                osm_id=self.location_osm_id,
                osm_type=self.location_osm_type,
            )
            self.location = location

    def save(self, *args, **kwargs):
        self.full_clean()
        self.set_location()
        super().save(*args, **kwargs)

    @property
    def file_path_full(self):
        if self.file_path:
            return str(settings.IMAGES_DIR / self.file_path)
        return None

    @property
    def image_thumb_path_full(self):
        if self.image_thumb_path:
            return str(settings.IMAGES_DIR / self.image_thumb_path)
        return None

    @property
    def is_type_single_shop(self):
        return self.type in proof_constants.TYPE_SINGLE_SHOP_LIST

    def update_price_count(self):
        self.price_count = self.prices.count()
        self.save(update_fields=["price_count"])

    def update_location(self, location_osm_id, location_osm_type):
        old_location = self.location
        # update proof location
        self.location_osm_id = location_osm_id
        self.location_osm_type = location_osm_type
        self.set_location()
        self.save()
        self.refresh_from_db()
        new_location = self.location
        # update proof's prices location?
        # # done in post_save signal
        # update old & new location price counts
        if old_location:
            old_location.update_price_count()
        if new_location:
            new_location.update_price_count()

    def set_missing_fields_from_prices(self):
        fields_to_update = list()
        if self.is_type_single_shop and self.prices.exists():
            for field in Proof.FIX_PRICE_FIELDS:
                if not getattr(self, field):
                    proof_prices_field_list = list(
                        self.prices.values_list(field, flat=True).distinct()
                    )
                    if len(proof_prices_field_list) == 1:
                        if field == "location":
                            location = self.prices.first().location
                            self.location_osm_id = location.osm_id
                            self.location_osm_type = location.osm_type
                            fields_to_update.extend(
                                ["location_osm_id", "location_osm_type"]
                            )
                        else:
                            setattr(self, field, getattr(self.prices.first(), field))
                            fields_to_update.append(field)
                    else:
                        print(
                            f"different {field}s",
                            self,
                            f"{self.prices.count()} prices",
                            proof_prices_field_list,
                        )
        if len(fields_to_update):
            self.save()


@receiver(signals.post_save, sender=Proof)
def proof_post_save_run_ocr(sender, instance, created, **kwargs):
    if not settings.TESTING:
        if created:
            async_task(
                "open_prices.proofs.utils.fetch_and_save_ocr_data",
                f"{settings.IMAGES_DIR}/{instance.file_path}",
            )


@receiver(signals.post_save, sender=Proof)
def proof_post_save_update_prices(sender, instance, created, **kwargs):
    if not created:
        if instance.is_type_single_shop and instance.prices.exists():
            from open_prices.prices.models import Price

            for price in instance.prices.all():
                for field in Price.DUPLICATE_PROOF_FIELDS:
                    setattr(price, field, getattr(instance, field))
                    price.save()


@receiver(signals.post_delete, sender=Proof)
def proof_post_delete_remove_images(sender, instance, **kwargs):
    import os

    if instance.file_path_full:
        if os.path.exists(instance.file_path_full):
            os.remove(instance.file_path_full)
    if instance.image_thumb_path_full:
        if os.path.exists(instance.image_thumb_path_full):
            os.remove(instance.image_thumb_path_full)


class ProofPrediction(models.Model):
    """A machine learning prediction for a proof."""

    proof = models.ForeignKey(
        Proof,
        on_delete=models.CASCADE,
        related_name="predictions",
        verbose_name="The proof this prediction belongs to",
    )
    type = models.CharField(
        max_length=20,
        choices=proof_constants.PROOF_TYPE_CHOICES,
        verbose_name="The type of the prediction",
    )
    model_name = models.CharField(
        max_length=30,
        verbose_name="The name of the model that generated the prediction",
    )
    model_version = models.CharField(
        max_length=30,
        verbose_name="The specific version of the model that generated the prediction",
    )
    created = models.DateTimeField(
        default=timezone.now, verbose_name="When the prediction was created in DB"
    )
    data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="a dict representing the data of the prediction. This field is model-specific.",
    )
    value = models.CharField(
        null=True,
        blank=True,
        max_length=30,
        verbose_name="The predicted value, only for classification models, null otherwise.",
    )
    max_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name="The maximum confidence of the prediction, may be null for some models."
        "For object detection models, this is the confidence of the most confident object."
        "For classification models, this is the confidence of the predicted class.",
    )

    class Meta:
        db_table = "proof_predictions"
        verbose_name = "Proof Prediction"
        verbose_name_plural = "Proof Predictions"

    def __str__(self):
        return f"{self.model_name} - {self.model_version} - {self.proof}"


@receiver(signals.post_save, sender=Proof)
def proof_post_save_run_ml_models(sender, instance, created, **kwargs):
    """After saving a proof in DB, run ML models on it.

    Currently, only the proof classification model is run.
    """
    if not settings.TESTING and settings.ENABLE_ML_PREDICTIONS:
        if created:
            async_task(
                "open_prices.proofs.ml.run_and_save_proof_prediction",
                instance.id,
            )


class PriceTag(models.Model):
    """A single price tag in a proof."""

    UPDATE_FIELDS = ["bounding_box", "status", "price_id"]
    CREATE_FIELDS = UPDATE_FIELDS + ["proof_id"]

    proof = models.ForeignKey(
        Proof,
        on_delete=models.CASCADE,
        related_name="price_tags",
        help_text="The proof this price tag belongs to",
    )
    price = models.ForeignKey(
        "prices.Price",
        on_delete=models.SET_NULL,
        related_name="price_tags",
        null=True,
        blank=True,
        help_text="The price linked to this tag",
    )
    created = models.DateTimeField(
        default=timezone.now, help_text="When the tag was created in DB"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="When the tag was last updated"
    )
    bounding_box = ArrayField(
        base_field=models.FloatField(),
        help_text="Coordinates of the bounding box, in the format [y_min, x_min, y_max, x_max]",
    )
    status = models.IntegerField(
        choices=constants.PRICE_TAG_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="The annotation status",
    )
    model_version = models.CharField(
        max_length=30,
        help_text="The version of the object detector model that generated the prediction",
        blank=True,
        null=True,
    )
    created_by = models.CharField(
        max_length=100,
        help_text="The name of the user who created this price tag. This field is null if "
        "the tag was created by a model.",
        null=True,
        blank=True,
    )
    updated_by = models.CharField(
        max_length=100,
        help_text="The name of the user who last updated this price tag bounding boxes. "
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
