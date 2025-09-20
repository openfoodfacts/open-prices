import datetime
import decimal

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Q, Value, When, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task

from open_prices.challenges.models import Challenge
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

    def has_type_group_single_shop(self):
        return self.filter(type__in=proof_constants.TYPE_GROUP_SINGLE_SHOP_LIST)

    def has_kind_community(self):
        return self.exclude(owner_consumption=True)

    def has_kind_consumption(self):
        return self.filter(
            type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST, owner_consumption=True
        )

    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_extra_fields(self):
        return self.annotate(
            kind_annotated=Case(
                When(
                    type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
                    owner_consumption=True,
                    then=Value(constants.KIND_CONSUMPTION),
                ),
                default=Value(constants.KIND_COMMUNITY),
                output_field=models.CharField(),
            ),
            source_annotated=Case(
                When(
                    source__contains="Open Prices Web App",
                    then=Value(constants.SOURCE_WEB),
                ),
                When(
                    source__contains="Smoothie",
                    then=Value(constants.SOURCE_MOBILE),
                ),
                When(source__contains="API", then=Value(constants.SOURCE_API)),
                default=Value(constants.SOURCE_OTHER),
                output_field=models.CharField(),
            ),
        )

    def with_stats(self):
        return (
            self.prefetch_related("prices", "price_tags", "receipt_items")
            .annotate(price_count_annotated=Count("prices", distinct=True))
            .annotate(price_tag_count_annotated=Count("price_tags", distinct=True))
            .annotate(
                receipt_item_count_annotated=Count("receipt_items", distinct=True)
            )
        )

    def has_tag(self, tag: str):
        return self.filter(tags__contains=[tag])

    def in_challenge(self, challenge: Challenge):
        return (
            self.prefetch_related("prices")
            .filter(prices__tags__contains=[challenge.tag])
            .distinct()
        )

    def duplicates(self, ref_proof):
        """
        Input: a reference proof
        Output: all proofs that have the same owner, date, type, and location_id  # noqa
        """
        return self.filter(
            type=ref_proof.type,
            location_id=ref_proof.location_id,
            date=ref_proof.date,
            owner=ref_proof.owner,
        ).exclude(id=ref_proof.id)
        # TODO: add md5 check


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
        "receipt_online_delivery_costs",
        "ready_for_price_tag_validation",
        "owner_consumption",
        "owner_comment",
    ]
    CREATE_FIELDS = UPDATE_FIELDS + [
        "location_id",  # extra field (optional)
    ]
    FIX_PRICE_FIELDS = ["location", "date", "currency"]
    DUPLICATE_LOCATION_FIELDS = [
        "location_osm_id",
        "location_osm_type",
    ]
    COUNT_FIELDS = ["price_count", "prediction_count"]

    file_path = models.CharField(blank=True, null=True)
    mimetype = models.CharField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=proof_constants.TYPE_CHOICES)

    image_md5_hash = models.CharField(
        max_length=32, blank=True, null=True, db_index=True
    )
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
        decimal_places=3,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )
    receipt_online_delivery_costs = models.DecimalField(
        verbose_name="Receipt's online delivery costs (user input)",
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )

    ready_for_price_tag_validation = models.BooleanField(default=False)

    owner_consumption = models.BooleanField(blank=True, null=True)
    owner_comment = models.TextField(blank=True, null=True)

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    prediction_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    tags = ArrayField(base_field=models.CharField(), blank=True, default=list)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(ProofQuerySet)()

    class Meta:
        db_table = "proofs"
        verbose_name = "Proof"
        verbose_name_plural = "Proofs"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # proof rules
        # - should have the right format
        # - should not be in the future (we accept 1 day leniency for users in future time zones)  # noqa
        if self.date:
            if type(self.date) is str:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "date",
                    "Parsing error. Expected format: YYYY-MM-DD",
                )
            elif self.date > timezone.now().date() + datetime.timedelta(days=1):
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
        # price-tag specific rules
        if not self.type == proof_constants.TYPE_PRICE_TAG:
            if self.ready_for_price_tag_validation:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "ready_for_price_tag_validation",
                    "Can only be set if type PRICE_TAG",
                )
        # receipt specific rules
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
            if self.receipt_online_delivery_costs is not None:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "receipt_online_delivery_costs",
                    "Can only be set if type RECEIPT",
                )
        # consumption specific rules
        if self.type not in proof_constants.TYPE_GROUP_CONSUMPTION_LIST:
            if self.owner_consumption is not None:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "owner_consumption",
                    f"Can only be set if type is consumption ({proof_constants.TYPE_GROUP_CONSUMPTION_LIST})",
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
        return self.type in proof_constants.TYPE_GROUP_SINGLE_SHOP_LIST

    @property
    def kind(self):
        if self.owner_consumption:
            return constants.KIND_CONSUMPTION
        return constants.KIND_COMMUNITY

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

    def set_tag(self, tag: str, save: bool = True):
        if tag not in self.tags:
            self.tags.append(tag)
            if save:
                self.save(update_fields=["tags"])
            return True
        return False

    def in_challenge(self, challenge: Challenge):
        return self.prices.filter(tags__contains=[challenge.tag]).exists()


@receiver(signals.post_save, sender=Proof)
def proof_post_save_run_ocr(sender, instance, created, **kwargs):
    if not settings.TESTING:
        if created:
            async_task(
                "open_prices.proofs.ml.fetch_and_save_ocr_data",
                f"{settings.IMAGES_DIR}/{instance.file_path}",
            )


@receiver(signals.post_save, sender=Proof)
def proof_post_save_run_ml_models(sender, instance, created, **kwargs):
    """
    After saving a proof in DB, run ML models on it.
    - type prediction
    - price tags extraction
    """
    if not settings.TESTING and settings.ENABLE_ML_PREDICTIONS:
        if created:
            async_task(
                "open_prices.proofs.ml.run_and_save_proof_prediction",
                instance,
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
        choices=proof_constants.PROOF_PREDICTION_TYPE_CHOICES,
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

    created = models.DateTimeField(
        default=timezone.now, verbose_name="When the prediction was created in DB"
    )

    class Meta:
        db_table = "proof_predictions"
        verbose_name = "Proof Prediction"
        verbose_name_plural = "Proof Predictions"

    def __str__(self):
        return f"{self.proof} - {self.model_name} - {self.model_version}"


@receiver(signals.post_save, sender=ProofPrediction)
def proof_prediction_post_create_increment_counts(sender, instance, created, **kwargs):
    if created:
        if instance.proof_id:
            Proof.objects.filter(id=instance.proof_id).update(
                prediction_count=F("prediction_count") + 1
            )


class PriceTagQuerySet(models.QuerySet):
    def status_unknown(self):
        return self.filter(status=None)

    def status_linked_to_price(self):
        return self.filter(status=proof_constants.PriceTagStatus.linked_to_price.value)

    def has_price_product_name_empty(self):
        return self.select_related("price").filter(
            Q(price__product_name=None) | Q(price__product_name="")
        )

    def has_tag(self, tag: str):
        return self.filter(tags__contains=[tag])


class PriceTag(models.Model):
    """A single price tag in a proof."""

    UPDATE_FIELDS = ["bounding_box", "status", "price_id"]
    CREATE_FIELDS = UPDATE_FIELDS + ["proof_id"]
    COUNT_FIELDS = ["prediction_count"]

    proof = models.ForeignKey(
        Proof,
        on_delete=models.CASCADE,
        related_name="price_tags",
        help_text="The proof this price tag belongs to",
    )
    proof_prediction = models.ForeignKey(
        ProofPrediction,
        on_delete=models.SET_NULL,
        related_name="price_tags",
        null=True,
        blank=True,
        help_text="The proof prediction used to create this price tag. Null if created by a user.",
    )
    price = models.ForeignKey(
        "prices.Price",
        on_delete=models.SET_NULL,
        related_name="price_tags",
        null=True,
        blank=True,
        help_text="The price linked to this tag",
    )
    bounding_box = ArrayField(
        base_field=models.FloatField(),
        help_text="Coordinates of the bounding box, in the format [y_min, x_min, y_max, x_max]",
    )
    status = models.IntegerField(
        choices=proof_constants.PRICE_TAG_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="The annotation status",
    )

    prediction_count = models.PositiveIntegerField(default=0, blank=True, null=True)

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

    tags = ArrayField(base_field=models.CharField(), blank=True, default=list)

    created = models.DateTimeField(
        default=timezone.now, help_text="When the tag was created in DB"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="When the tag was last updated"
    )

    objects = models.Manager.from_queryset(PriceTagQuerySet)()

    class Meta:
        db_table = "price_tags"
        verbose_name = "Price Tag"
        verbose_name_plural = "Price Tags"

    def __str__(self):
        return f"{self.proof} - {self.id} - {self.status}"

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

        # self.proof and self.price are fetched with select_related in the view
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

        if self.proof_prediction:
            if self.proof_prediction.proof_id != self.proof.id:
                utils.add_validation_error(
                    validation_errors,
                    "proof_prediction",
                    "Proof prediction should belong to the same proof.",
                )

        if self.price:
            if self.proof and self.price.proof_id != self.proof.id:
                utils.add_validation_error(
                    validation_errors,
                    "price",
                    "Price should belong to the same proof.",
                )
            if self.status is None:
                self.status = proof_constants.PriceTagStatus.linked_to_price.value
            elif self.status != proof_constants.PriceTagStatus.linked_to_price.value:
                utils.add_validation_error(
                    validation_errors,
                    "status",
                    "Status should be `linked_to_price` when price_id is set.",
                )

        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def set_tag(self, tag: str, save: bool = True):
        if tag not in self.tags:
            self.tags.append(tag)
            if save:
                self.save(update_fields=["tags"])
            return True
        return False

    def update_tags(self):
        changes = False
        # prediction tags
        from open_prices.proofs.ml import (
            price_tag_prediction_has_predicted_barcode_valid,
            price_tag_prediction_has_predicted_category_tag_valid,
            price_tag_prediction_has_predicted_product_exists,
        )

        if self.predictions.exists():
            prediction = self.predictions.first()
            if price_tag_prediction_has_predicted_barcode_valid(prediction):
                changes = self.set_tag(
                    proof_constants.PRICE_TAG_PREDICTION_TAG_BARCODE_VALID, save=False
                )
            if price_tag_prediction_has_predicted_product_exists(prediction):
                changes = self.set_tag(
                    proof_constants.PRICE_TAG_PREDICTION_TAG_PRODUCT_EXISTS, save=False
                )
            if price_tag_prediction_has_predicted_category_tag_valid(prediction):
                changes = self.set_tag(
                    proof_constants.PRICE_TAG_PREDICTION_TAG_CATEGORY_TAG_VALID,
                    save=False,
                )
        # save
        if changes:
            self.save(update_fields=["tags"])

    def get_predicted_price(self) -> float | None:
        if self.predictions.exists():
            prediction = self.predictions.first()
            if prediction.schema_version == "1.0":
                return prediction.data.get("price")
            elif prediction.schema_version == "2.0":
                return (prediction.data.get("selected_price") or {}).get("price")
        return None

    def get_predicted_barcode(self):
        if self.predictions.exists():
            prediction = self.predictions.first()
            return prediction.data.get("barcode")
        return None

    def get_predicted_category(self):  # category_tag
        if self.predictions.exists():
            prediction = self.predictions.first()
            if prediction.schema_version == "1.0":
                return prediction.data.get("product")
            elif prediction.schema_version == "2.0":
                return prediction.data.get("category")
        return None

    def get_predicted_product_name(self):
        if self.predictions.exists():
            return self.predictions.first().data.get("product_name")
        return None


class PriceTagPrediction(models.Model):
    """A machine learning prediction for a price tag."""

    price_tag = models.ForeignKey(
        PriceTag,
        on_delete=models.CASCADE,
        related_name="predictions",
        help_text="The price tag this prediction belongs to",
    )
    type = models.CharField(
        max_length=20,
        choices=proof_constants.PRICE_TAG_PREDICTION_TYPE_CHOICES,
        help_text="The type of the prediction",
    )
    model_name = models.CharField(
        max_length=30,
        help_text="The name of the model that generated the prediction",
    )
    model_version = models.CharField(
        max_length=30,
        help_text="The specific version of the model that generated the prediction",
    )
    schema_version = models.CharField(
        null=True,
        blank=True,
        max_length=20,
        help_text="The schema version of the prediction data. Used to handle changes in the "
        "prediction data structure. It is currently used when calling Gemine API to extract price tags.",
    )
    data = models.JSONField(
        null=False,
        blank=False,
        help_text="a dict representing the data of the prediction. This field is model-specific.",
        default=dict,
    )
    thought_tokens = models.TextField(
        null=True,
        blank=True,
        help_text="The thought tokens generated by the model, if available. This is used to "
        "provide insights into the model's reasoning process.",
    )

    created = models.DateTimeField(
        default=timezone.now, help_text="When the prediction was created in DB"
    )

    class Meta:
        db_table = "price_tag_predictions"
        verbose_name = "Price Tag Prediction"
        verbose_name_plural = "Price Tag Predictions"

    def __str__(self):
        return f"{self.price_tag} - {self.model_name} - {self.model_version}"

    def has_predicted_barcode_valid(self):
        return (
            proof_constants.PRICE_TAG_PREDICTION_TAG_BARCODE_VALID
            in self.price_tag.tags
        )

    def has_predicted_product_exists(self):
        return (
            proof_constants.PRICE_TAG_PREDICTION_TAG_PRODUCT_EXISTS
            in self.price_tag.tags
        )

    def has_predicted_barcode_valid_and_product_exists(self):
        return (
            self.has_predicted_barcode_valid() and self.has_predicted_product_exists()
        )

    def has_predicted_category_tag_valid(self):
        return (
            proof_constants.PRICE_TAG_PREDICTION_TAG_CATEGORY_TAG_VALID
            in self.price_tag.tags
        )


@receiver(signals.post_save, sender=PriceTagPrediction)
def price_tag_prediction_post_create_increment_counts(
    sender, instance, created, **kwargs
):
    if created:
        if instance.price_tag_id:
            PriceTag.objects.filter(id=instance.price_tag_id).update(
                prediction_count=F("prediction_count") + 1
            )


@receiver(signals.post_save, sender=PriceTagPrediction)
def price_tag_prediction_post_create_update_price_tag_tags(
    sender, instance, created, **kwargs
):
    if created:
        if instance.price_tag_id:
            instance.price_tag.update_tags()


class ReceiptItemQuerySet(models.QuerySet):
    def status_unknown(self):
        return self.filter(status=None)

    def status_linked_to_price(self):
        return self.filter(
            status=proof_constants.ReceiptItemStatus.linked_to_price.value
        )

    def has_price_product_name_empty(self):
        return self.select_related("price").filter(
            Q(price__product_name=None) | Q(price__product_name="")
        )


class ReceiptItem(models.Model):
    """A single receipt item."""

    CREATE_FIELDS = ["status", "proof_id", "price_id", "order"]

    proof = models.ForeignKey(
        Proof,
        on_delete=models.CASCADE,
        related_name="receipt_items",
        help_text="The proof this receipt item belongs to",
    )
    proof_prediction = models.ForeignKey(
        ProofPrediction,
        on_delete=models.SET_NULL,
        related_name="receipt_items",
        null=True,
        blank=True,
        help_text="The proof prediction used to create this receipt item. Null if created by a user.",
    )
    price = models.ForeignKey(
        "prices.Price",
        on_delete=models.SET_NULL,
        related_name="receipt_items",
        null=True,
        blank=True,
        help_text="The price linked to this receipt item",
    )
    order = models.IntegerField(
        help_text="The order of the item in the receipt. Item on top is 1.",
    )
    predicted_data = models.JSONField(
        null=False,
        blank=False,
        help_text="A dict representing the predicted data of the receipt item. For example the product name, the price etc.",
        default=dict,
    )
    status = models.CharField(
        choices=proof_constants.RECEIPT_ITEM_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="The current status of the item",
    )

    created = models.DateTimeField(
        default=timezone.now, help_text="When the item was created in DB"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="When the item was last updated"
    )

    objects = models.Manager.from_queryset(ReceiptItemQuerySet)()

    class Meta:
        db_table = "receipt_items"
        verbose_name = "Receipt Item"
        verbose_name_plural = "Receipt Items"

    def get_predicted_price(self):
        return self.predicted_data.get("price")

    def get_predicted_product_name(self):
        return self.predicted_data.get("product_name")
