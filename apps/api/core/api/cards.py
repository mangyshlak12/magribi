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


@extend_schema(request=TokenInput, responses={200: CardOutput, 201: CardOutput})
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_card(request):
    data = validated(TokenInput, request.data)
    card, created = Card.objects.get_or_create(token_hash=token_hash(data["token"]))
    return Response(card_result(card), status=201 if created else 200)


@extend_schema(responses=CardOutput)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def current_card(request):
    return Response(card_result(bearer_card(request)))


@extend_schema(responses=HistoryOutput)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def card_history(request):
    return Response(operation_page(bearer_card(request).operations.all(), request))
