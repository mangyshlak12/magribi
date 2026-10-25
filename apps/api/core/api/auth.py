from drf_spectacular.utils import extend_schema
from .schema import (
    CardOutput,
    StaffOutput,
    BranchOutput,
    OperationOutput,
    HistoryOutput,
    MutationOutput,
    OkOutput,
    SummaryOutput,
)
import hashlib, json
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.db import connection, transaction
from django.db.models import Q, Sum, Count, Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import Card, Operation, Branch, User, LoginFailure
from ..permissions import StaffPermission, ManagerPermission
from ..serializers import (
    TokenInput,
    TransactionInput,
    ReversalInput,
    StaffInput,
    StaffStatusInput,
    BranchInput,
)
from ..services import token_hash, card_result, operation_result, record_operation
from ..exceptions import BusinessError

from .common import validated, user_result, bearer_card, operation_page


@require_http_methods(["GET"])
def health(request):
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@csrf_protect
@require_http_methods(["POST"])
def staff_login(request):
    try:
        data = json.loads(request.body)
        username, password = data.get("username", ""), data.get("password", "")
        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or len(username) > 150
            or len(password) > 128
        ):
            raise ValueError()
        username = username.strip().lower()
    except (ValueError, AttributeError):
        return JsonResponse({"detail": "Логин мен құпиясөзді енгізіңіз"}, status=400)
    # Proxy headers are not trusted for rate-limit identity. Configure a trusted ingress if needed.
    digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
    uh, ih = digest(username), digest(request.META.get("REMOTE_ADDR", "unknown"))
    failures = LoginFailure.objects.filter(
        created_at__gte=timezone.now() - timedelta(minutes=15)
    )
    if (
        failures.filter(username_hash=uh).count() >= 8
        or failures.filter(ip_hash=ih).count() >= 50
    ):
        return JsonResponse(
            {"detail": "Тым көп әрекет. 15 минуттан кейін қайталаңыз"}, status=429
        )
    user = authenticate(request, username=username, password=password)
    if not user or not user.is_active:
        LoginFailure.objects.create(username_hash=uh, ip_hash=ih)
        return JsonResponse({"detail": "Логин немесе құпиясөз дұрыс емес"}, status=400)
    login(request, user)
    return JsonResponse(user_result(user))


@extend_schema(request=None, responses=OkOutput)
@api_view(["POST"])
@permission_classes([StaffPermission])
def staff_logout(request):
    logout(request)
    return Response({"ok": True})


@extend_schema(responses=StaffOutput)
@api_view(["GET"])
@permission_classes([StaffPermission])
def me(request):
    return Response(user_result(request.user))
