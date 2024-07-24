import requests
from django.conf import settings


def off_authenticate(username, password):
    data = {"user_id": username, "password": password, "body": 1}
    return requests.post(f"{settings.OAUTH2_SERVER_URL}", data=data)
