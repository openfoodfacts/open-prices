from django.db.models import IntegerField, Model, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce


def count_subquery(model: type[Model], field: str, aggregate):
    """
    Aggregate over the model rows related to the outer row (0 if none).
    Example: count_subquery(Price, "product", Count("id"))
    = the number of prices of each product
    """
    return Coalesce(
        Subquery(
            model.objects.filter(**{field: OuterRef("pk")})
            .order_by()
            .values(field)
            .annotate(value=aggregate)
            .values("value")
        ),
        0,
        output_field=IntegerField(),
    )


def update_counts(obj: Model, queryset: QuerySet, count_fields: list):
    """
    Update the count fields of a single object, from a queryset annotated
    with the "<count field>_annotated" values (see the with_*_count() methods)
    """
    obj_annotated = queryset.get(pk=obj.pk)
    for field in count_fields:
        setattr(obj, field, getattr(obj_annotated, f"{field}_annotated"))
    obj.save(update_fields=count_fields)


def bulk_update_counts(
    queryset: QuerySet, count_fields: list, batch_size: int = 1000
) -> int:
    """
    Update the count fields of the queryset objects, in batches, from the
    "<count field>_annotated" values (see the with_*_count() methods)
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
        objs_to_update = list()
        for obj in batch:
            new_counts = {
                field: getattr(obj, f"{field}_annotated") for field in count_fields
            }
            if any(getattr(obj, field) != new_counts[field] for field in count_fields):
                for field, value in new_counts.items():
                    setattr(obj, field, value)
                objs_to_update.append(obj)
        if objs_to_update:
            model.objects.bulk_update(objs_to_update, count_fields)
            updated_count += len(objs_to_update)
    return updated_count
