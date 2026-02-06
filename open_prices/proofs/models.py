import decimal
import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Q, Value, When, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from simple_history.models import HistoricalRecords

from open_prices.challenges.models import Challenge

# Import custom lookups so that they are registered
from open_prices.common import (
    constants,
    history,
    lookups,  # noqa: F401
    utils,
)
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.proofs import constants as proof_constants
from open_prices.proofs import validators as proof_validators
from open_prices.users.models import User


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

    def calculate_field_distinct_count(self, field_name: str):
        return (
            self.exclude(**{f"{field_name}__isnull": True})
            .values(field_name)
            .distinct()
            .count()
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

    # denormalized counts (updated with signals and/or cronjobs)
    price_count = models.PositiveIntegerField(default=0)
    prediction_count = models.PositiveIntegerField(default=0)

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    tags = ArrayField(base_field=models.CharField(), blank=True, default=list)
    flags = GenericRelation("moderation.Flag", related_query_name="proof")

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(
        excluded_fields=COUNT_FIELDS,
        get_user=history.get_history_user_from_request,
        history_user_id_field=models.CharField(null=True),
        history_user_getter=history.history_user_getter,
        history_user_setter=history.history_user_setter,
        # cascade_delete_history=False,  # default
    )

    objects = models.Manager.from_queryset(ProofQuerySet)()

    class Meta:
        db_table = "proofs"
        verbose_name = "Proof"
        verbose_name_plural = "Proofs"

    def clean(self, *args, **kwargs):
        # store all ValidationError in a dict
        validation_errors = utils.merge_validation_errors(
            proof_validators.validate_proof_date_rules(self),
            proof_validators.validate_proof_location_rules(self),
            proof_validators.validate_proof_type_price_tag_rules(self),
            proof_validators.validate_proof_type_receipt_rules(self),
            proof_validators.validate_proof_type_consumption_rules(self),
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
        """
        - run validations
        - set location (create if needed)
        """
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
        self._change_reason = "Proof.update_location() method"
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
            self._change_reason = "Proof.set_missing_fields_from_prices() method"
            self.save()

    def set_tag(self, tag: str, save: bool = True):
        if tag not in self.tags:
            self.tags.append(tag)
            if save:
                self._change_reason = "Proof.set_tag() method"
                self.save(update_fields=["tags"])
            return True
        return False

    def in_challenge(self, challenge: Challenge):
        return self.prices.filter(tags__contains=[challenge.tag]).exists()

    def get_history_list(self):
        return history.build_instance_history_list(self)


@receiver(signals.post_save, sender=Proof)
def proof_post_create_increment_counts(sender, instance, created, **kwargs):
    if created:
        if instance.owner:
            User.objects.filter(user_id=instance.owner).update(
                proof_count=F("proof_count") + 1
            )
        if instance.location_id:
            Location.objects.filter(id=instance.location_id).update(
                proof_count=F("proof_count") + 1
            )
    else:
        # what about if we update location? (owner cannot be updated)
        # the update_fields is often not set, so we cannot rely on it
        pass


@receiver(signals.post_save, sender=Proof)
def proof_post_save_run_ocr(sender, instance, created, **kwargs):
    if not settings.TESTING and settings.ENABLE_OCR:
        if created:
            async_task(
                "open_prices.proofs.ml.ocr.fetch_and_save_ocr_data",
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
                    price._change_reason = "Proof.update_location() method"
                    price.save()


@receiver(signals.post_delete, sender=Proof)
def proof_post_delete_decrement_counts(sender, instance, **kwargs):
    if instance.owner:
        User.objects.filter(user_id=instance.owner, proof_count__gt=0).update(
            proof_count=F("proof_count") - 1
        )
    if instance.location_id:
        Location.objects.filter(id=instance.location.id, proof_count__gt=0).update(
            proof_count=F("proof_count") - 1
        )


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

    prediction_count = models.PositiveIntegerField(default=0)

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
        # store all ValidationError in a dict
        validation_errors = utils.merge_validation_errors(
            proof_validators.validate_price_tag_bounding_box_rules(self),
            proof_validators.validate_price_tag_relationship_rules(self),
        )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        - run validations
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def image_path(self):
        from open_prices.proofs.utils import get_price_tag_image_path

        return get_price_tag_image_path(self.id)

    @property
    def image_path_full(self):
        return str(settings.IMAGES_DIR / self.image_path)

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
        from open_prices.proofs.ml.price_tags import (
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


@receiver(signals.post_save, sender=PriceTag)
def price_tag_post_save_generate_image(sender, instance, created, **kwargs):
    from open_prices.proofs.utils import generate_price_tag_image

    update_fields = kwargs.get("update_fields")
    if (
        created
        or (update_fields and "bounding_box" in update_fields)
        or update_fields is None
    ):
        # Cropping is fast, run synchronously
        generate_price_tag_image(instance)


@receiver(signals.post_delete, sender=PriceTag)
def price_tag_post_delete_remove_image(sender, instance, **kwargs):
    if os.path.exists(instance.image_path_full):
        try:
            os.remove(instance.image_path_full)
        except OSError:
            pass


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
        "prediction data structure. It is currently used when calling Gemini API to extract price tags.",
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
    schema_version = models.CharField(
        null=True,
        blank=True,
        max_length=20,
        help_text="The schema version of the predicted data. Used to handle changes in the "
        "prediction data structure.",
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
