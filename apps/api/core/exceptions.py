from rest_framework.views import exception_handler as drf_handler
from rest_framework.response import Response


class BusinessError(Exception):
    def __init__(self, message, status=409):
        self.message, self.status = message, status


def exception_handler(exc, context):
    if isinstance(exc, BusinessError):
        return Response({"detail": exc.message}, status=exc.status)
    return drf_handler(exc, context)
