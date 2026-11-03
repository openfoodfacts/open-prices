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
    pk_name = model._meta.pk.name
    queryset = queryset.only(pk_name, *count_fields).order_by(pk_name)
    last_pk = None
    updated_count = 0
    while True:
        batch_queryset = queryset
        if last_pk is not None:
            batch_queryset = queryset.filter(pk__gt=last_pk)
        batch = list(batch_queryset[:batch_size])
        if not batch:
            break
        last_pk = batch[-1].pk
        counts = get_counts([obj.pk for obj in batch])
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
