def get_history_user_from_request(request, **kwargs):
    """
    Custom function to get the history user from the request.
    This function is used to override the default behavior
    to store a string instead of a User instance.
    https://github.com/django-commons/django-simple-history/blob/master/simple_history/models.py
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user.user_id
    return None


def history_user_getter(instance):
    """
    Override the default history user getter to use 'history_user_id' field.
    https://django-simple-history.readthedocs.io/en/stable/user_tracking.html#manually-track-user-model
    """
    return instance.history_user_id


def history_user_setter(instance, user_id):
    """
    Override the default history user setter to use 'history_user_id' field.
    https://django-simple-history.readthedocs.io/en/stable/user_tracking.html#manually-track-user-model
    """
    instance.history_user_id = user_id
