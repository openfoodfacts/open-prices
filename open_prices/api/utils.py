from django.http import Http404


def get_object_or_drf_404(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise Http404(f"No {model._meta.verbose_name} matches the given query.")
