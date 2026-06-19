import django_filters
from django.core.validators import EMPTY_VALUES
from django.http import Http404


class ArrayFieldElementContainsFilter(django_filters.CharFilter):
    """
    Input: tags__contains=en:organic
    Output: tags__contains=['en:organic']
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("lookup_expr", "contains")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        return super().filter(qs, [value])


def get_object_or_drf_404(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise Http404(
            f"No {model._meta.verbose_name} matches the given query."
        ) from None


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
