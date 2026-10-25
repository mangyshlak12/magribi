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


def validated(cls, data):
    obj = cls(data=data)
    obj.is_valid(raise_exception=True)
    return obj.validated_data


def user_result(u):
    return {
        "id": u.id,
        "username": u.username,
        "name": u.first_name,
        "role": u.role,
        "is_active": u.is_active,
        "branch_id": str(u.branch_id) if u.branch_id else None,
        "branch": u.branch.name if u.branch_id else None,
    }


def bearer_card(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise BusinessError("Карта сілтемесін ашыңыз", 401)
    return get_object_or_404(Card, token_hash=token_hash(header[7:]))


def page_number(request):
    try:
        return max(1, min(int(request.query_params.get("page", 1)), 10000))
    except ValueError:
        raise BusinessError("Бет нөмірі жарамсыз", 400)


def operation_page(qs, request, staff=False):
    page = page_number(request)
    offset = (page - 1) * 25
    rows = list(
        qs.select_related("actor", "branch").annotate(
            has_reversal=Exists(Operation.objects.filter(reverses_id=OuterRef("pk")))
        )[offset : offset + 26]
    )
    items = [operation_result(o) for o in rows[:25]]
    if not staff:
        for item in items:
            item.pop("actor", None)
            item.pop("reason", None)
            item.pop("card_id", None)
    return {"items": items, "page": page, "has_more": len(rows) > 25}
