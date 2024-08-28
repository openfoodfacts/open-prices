from django.core import exceptions
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: View):
    """
    Custom exception handler for DRF
    To better handle Django ValidationError
    source: https://stackoverflow.com/a/61701513/4293684
    """
    response = exception_handler(exc, context)

    if isinstance(exc, exceptions.ValidationError):
        data = exc.message_dict
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    return response
