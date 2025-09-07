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
