from itertools import pairwise

from django.core.management import call_command

HISTORY_FIELDS = [
    "history_id",
    "history_date",
    "history_change_reason",
    "history_type",
    "history_user_id",
]

HISTORY_TYPE_CHOICES = [("+", "Created"), ("~", "Changed"), ("-", "Deleted")]


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


def history_clean_duplicate_command():
    """
    Management command to clean duplicate history entries.
    https://django-simple-history.readthedocs.io/en/stable/utils.html#clean-duplicate-history
    Why? A historical record is created on every save even if 0 fields changed.
    --auto: run on all models with HistoricalRecords
    --minutes: how far back in history searching for duplicates
    --verbosity 0: no output
    """
    two_days_in_minutes = 2 * 24 * 60
    call_command(
        "clean_duplicate_history",
        "--auto",
        "--minutes",
        f"{two_days_in_minutes}",
        "--verbosity",
        "0",
    )


def build_instance_history_list(instance):
    history_list = []
    instance_history = instance.history.all()  # ordered by -history_date

    # iterate over pairs of consecutive history records
    for new_record, old_record in pairwise(instance_history.iterator()):
        delta = new_record.diff_against(old_record)
        if delta.changes:
            history_entry = {
                field: getattr(new_record, field) for field in HISTORY_FIELDS
            }
            history_entry["changes"] = [
                {
                    "field": change.field,
                    "old": change.old,
                    "new": change.new,
                }
                for change in delta.changes
            ]
            history_list.append(history_entry)

    # append the initial creation entry
    history_entry = {
        field: getattr(instance_history.last(), field) for field in HISTORY_FIELDS
    }
    history_entry["changes"] = []
    history_list.append(history_entry)

    return history_list
