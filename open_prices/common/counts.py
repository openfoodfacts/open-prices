from django.db.models import IntegerField, Model, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce

ANNOTATED_SUFFIX = "_annotated"


def count_subquery(related_model: type[Model], related_field: str, aggregate):
    """
    Aggregate over the related model rows of the outer row (0 if none).
    Example: count_subquery(Price, "product", Count("id"))
    = the number of prices of each product
    """
    return Coalesce(
        Subquery(
            related_model.objects.filter(**{related_field: OuterRef("pk")})
            .order_by()
            .values(related_field)
            .annotate(value=aggregate)
            .values("value")
        ),
        0,
        output_field=IntegerField(),
    )


class CountsQuerySetMixin:
    def annotate_counts(
        self, related_model: type[Model], related_field: str, counts: dict
    ):
        """
        Annotate each count as "<count field>_annotated" on the queryset rows,
        aggregated over the related model rows
        (related_model.related_field = the row).
        Example: Product.objects.annotate_counts(
            related_model=Price,
            related_field="product",
            counts={"price_count": Count("id")},
        )
        = each product annotated with price_count_annotated
          (the number of prices with price.product = the product)
        """
        return self.annotate(
            **{
                f"{count_field}{ANNOTATED_SUFFIX}": count_subquery(
                    related_model, related_field, aggregate
                )
                for count_field, aggregate in counts.items()
            }
        )


def set_counts(obj: Model, obj_annotated: Model, count_fields: list) -> bool:
    """
    Copy the "<count field>_annotated" values of obj_annotated to obj.
    Returns True if a count changed.
    """
    changed = False
    for field in count_fields:
        value = getattr(obj_annotated, f"{field}{ANNOTATED_SUFFIX}")
        if getattr(obj, field) != value:
            setattr(obj, field, value)
            changed = True
    return changed


def update_counts(obj: Model, count_fields: list):
    """
    Update the count fields of a single object (see the with_counts() methods)
    """
    obj_annotated = type(obj).objects.with_counts().get(pk=obj.pk)
    set_counts(obj, obj_annotated, count_fields)
    obj.save(update_fields=count_fields)


def bulk_update_counts(
    queryset: QuerySet, count_fields: list, batch_size: int = 1000
) -> int:
    """
    Update the count fields of the queryset objects, in batches
    (see the with_counts() methods)
    - only the objects with changed counts are saved (with bulk_update,
      so without calling save() or sending signals)

    Returns the number of updated objects.
    """
    model = queryset.model
    pk_list = list(queryset.order_by("pk").values_list("pk", flat=True))
    updated_count = 0
    for i in range(0, len(pk_list), batch_size):
        batch = queryset.filter(pk__in=pk_list[i : i + batch_size]).only(
            model._meta.pk.name, *count_fields
        )
        objs_to_update = [obj for obj in batch if set_counts(obj, obj, count_fields)]
        if objs_to_update:
            model.objects.bulk_update(objs_to_update, count_fields)
            updated_count += len(objs_to_update)
    return updated_count
