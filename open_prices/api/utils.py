from django.http import Http404


def get_object_or_drf_404(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise Http404(f"No {model._meta.verbose_name} matches the given query.")


def get_source_from_request(request):
    app_name = request.GET.get("app_name", "API")
    app_version = request.GET.get("app_version", "")
    app_platform = request.GET.get("app_platform", "")
    app_page = request.GET.get("app_page", "")
    if app_version:
        app_name += f" ({app_version})"
    if app_platform:
        app_name += f" ({app_platform})"
    if app_page:
        app_name += f" - {app_page}"
    return app_name
