from django.db.models import QuerySet


def group_counts(queryset: QuerySet, group_field: str, **aggregates) -> dict:
    """
    Compute the aggregates grouped by group_field, in a single query.
    Returns a {group_field value: {aggregate name: value}} dict.
    """
    return {
        row.pop(group_field): row
        for row in queryset.order_by()
        .values(group_field)
        .annotate(**aggregates)
        .values(group_field, *aggregates.keys())
    }


def bulk_update_counts(
    queryset: QuerySet, count_fields: list, get_counts, batch_size: int = 1000
) -> int:
    """
    Update the count fields of the queryset objects, in batches.
    - get_counts(pk_list) must return a {pk: {count field: value}} dict
      (a missing pk or count field means 0)
    - only the objects with changed counts are saved (with bulk_update,
      so without calling save() or sending signals)

    Returns the number of updated objects.
    """
    model = queryset.model
    pk_list = list(queryset.order_by("pk").values_list("pk", flat=True))
    updated_count = 0
    for i in range(0, len(pk_list), batch_size):
        batch_pk_list = pk_list[i : i + batch_size]
        batch = model.objects.filter(pk__in=batch_pk_list).only(
            model._meta.pk.name, *count_fields
        )
        counts = get_counts(batch_pk_list)
        objs_to_update = list()
        for obj in batch:
            obj_counts = counts.get(obj.pk, {})
            new_counts = {field: obj_counts.get(field) or 0 for field in count_fields}
            if any(getattr(obj, field) != new_counts[field] for field in count_fields):
                for field, value in new_counts.items():
                    setattr(obj, field, value)
                objs_to_update.append(obj)
        if objs_to_update:
            model.objects.bulk_update(objs_to_update, count_fields)
            updated_count += len(objs_to_update)
    return updated_count
