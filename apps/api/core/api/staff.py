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


@extend_schema(request=TokenInput, responses=CardOutput)
@api_view(["POST"])
@permission_classes([StaffPermission])
def lookup(request):
    data = validated(TokenInput, request.data)
    card = get_object_or_404(Card, token_hash=token_hash(data["token"]))
    return Response(card_result(card, True))


@extend_schema(request=TransactionInput, responses=MutationOutput)
@api_view(["POST"])
@permission_classes([StaffPermission])
def purchase(request):
    data = validated(TransactionInput, request.data)
    get_object_or_404(Card, pk=data["card_id"])
    op = record_operation(actor=request.user, kind="purchase", **data)
    return Response(
        {
            "operation": operation_result(op),
            "card": card_result(Card.objects.get(pk=data["card_id"])),
            "ok": True,
        }
    )


@extend_schema(request=TransactionInput, responses=MutationOutput)
@api_view(["POST"])
@permission_classes([StaffPermission])
def redeem(request):
    data = validated(TransactionInput, request.data)
    get_object_or_404(Card, pk=data["card_id"])
    op = record_operation(actor=request.user, kind="redeem", **data)
    return Response(
        {
            "operation": operation_result(op),
            "card": card_result(Card.objects.get(pk=data["card_id"])),
            "ok": True,
        }
    )


@extend_schema(responses=HistoryOutput)
@api_view(["GET"])
@permission_classes([StaffPermission])
def operations(request):
    qs = Operation.objects.all()
    if request.user.role != "manager":
        qs = qs.filter(branch_id=request.user.branch_id)
    return Response(operation_page(qs, request, True))
