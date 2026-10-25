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


@extend_schema(request=ReversalInput, responses=MutationOutput)
@api_view(["POST"])
@permission_classes([ManagerPermission])
def reverse(request, operation_id):
    data = validated(ReversalInput, request.data)
    op = get_object_or_404(Operation, pk=operation_id)
    new = record_operation(
        actor=request.user,
        card_id=op.card_id,
        kind="reversal",
        quantity=op.quantity,
        reverses=op.id,
        **data,
    )
    return Response({"operation": operation_result(new), "ok": True})


@extend_schema(methods=["GET"], responses=StaffOutput(many=True))
@extend_schema(methods=["POST"], request=StaffInput, responses={201: StaffOutput})
@api_view(["GET", "POST"])
@permission_classes([ManagerPermission])
def staff_members(request):
    if request.method == "POST":
        data = validated(StaffInput, request.data)
        user = User.objects.create_user(
            username=data["username"].lower(),
            first_name=data["name"],
            password=data["password"],
            role=data["role"],
            branch=data["branch"],
        )
        return Response(user_result(user), status=201)
    return Response(
        [user_result(u) for u in User.objects.select_related("branch").order_by("id")]
    )


@extend_schema(request=StaffStatusInput, responses=StaffOutput)
@api_view(["PATCH"])
@permission_classes([ManagerPermission])
def staff_status(request, user_id):
    data = validated(StaffStatusInput, request.data)
    with transaction.atomic():
        # All manager changes acquire these locks in a stable order.
        managers = list(
            User.objects.select_for_update()
            .filter(role="manager", is_active=True)
            .order_by("id")
        )
        user = get_object_or_404(User.objects.select_for_update(), pk=user_id)
        if user.pk == request.user.pk:
            raise BusinessError("Өз аккаунтыңызды өшіре алмайсыз", 400)
        if not data["is_active"] and user.role == "manager" and len(managers) <= 1:
            raise BusinessError("Кемінде бір басқарушы қалуы керек")
        user.is_active = data["is_active"]
        user.save(update_fields=["is_active"])
    return Response(user_result(user))


@extend_schema(methods=["GET"], responses=BranchOutput(many=True))
@extend_schema(methods=["POST"], request=BranchInput, responses=BranchOutput(many=True))
@api_view(["GET", "POST"])
@permission_classes([ManagerPermission])
def branches(request):
    if request.method == "POST":
        data = validated(BranchInput, request.data)
        Branch.objects.create(**data)
    return Response(
        [
            {
                "id": str(b.id),
                "name": b.name,
                "address": b.address,
                "is_active": b.is_active,
            }
            for b in Branch.objects.order_by("created_at")
        ]
    )


@extend_schema(responses=SummaryOutput)
@api_view(["GET"])
@permission_classes([ManagerPermission])
def summary(request):
    sums = Operation.objects.aggregate(
        paid=Sum("paid_delta"), redeemed=Sum("redeemed_delta")
    )
    return Response(
        {
            "cards": Card.objects.count(),
            "paid_units": sums["paid"] or 0,
            "redeemed_units": sums["redeemed"] or 0,
            "operations": Operation.objects.count(),
            "cashiers": User.objects.filter(role="cashier", is_active=True).count(),
        }
    )
