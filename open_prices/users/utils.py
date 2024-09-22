from django.utils import timezone

from open_prices.users.models import Session, User


def get_or_create_session(user_id: str, token: str, is_moderator=False):
    user, user_created = User.objects.get_or_create(
        user_id=user_id, defaults={"is_moderator": is_moderator}
    )
    # update is_moderator if it has changed
    if not user_created and user.is_moderator != is_moderator:
        user.is_moderator = is_moderator
        user.save()
    session, session_created = Session.objects.get_or_create(user=user, token=token)
    session.last_used = timezone.now()
    session.save()


def get_session(token: str, update_last_used=True):
    session = Session.objects.get(token=token)
    if update_last_used:
        session.last_used = timezone.now()
        session.save()
    return session
