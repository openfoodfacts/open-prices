from django.utils import timezone

from open_prices.users.models import Session, User


def get_or_create_session(user_id: str, token: str):
    user, user_created = User.objects.get_or_create(user_id=user_id)
    session, session_created = Session.objects.get_or_create(user=user, token=token)
    session.last_used = timezone.now()
    session.save()


def get_session(token: str, update_last_used=True):
    session = Session.objects.get(token=token)
    if update_last_used:
        session.last_used = timezone.now()
        session.save()
    return session
