from django.http import Http404


def get_object_or_drf_404(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise Http404(f"No {model._meta.verbose_name} matches the given query.")


def get_source_from_request(request):
    app_name = request.GET.get("app_name", "API")
    app_version = request.GET.get("app_version", "")
    if app_version:
        return f"{app_name} ({app_version})"
    return app_name
