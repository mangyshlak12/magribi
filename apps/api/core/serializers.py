from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User, Branch


class TokenInput(serializers.Serializer):
    token = serializers.RegexField(r"^[A-Za-z0-9_-]{43}$")


class TransactionInput(serializers.Serializer):
    card_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    request_key = serializers.UUIDField()


class ReversalInput(serializers.Serializer):
    reason = serializers.CharField(min_length=5, max_length=500, trim_whitespace=True)
    request_key = serializers.UUIDField()


class StaffInput(serializers.Serializer):
    username = serializers.RegexField(r"^[a-zA-Z0-9_.-]{3,80}$")
    name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, max_length=128)
    role = serializers.ChoiceField(choices=["cashier", "manager"], default="cashier")
    branch_id = serializers.PrimaryKeyRelatedField(
        source="branch", queryset=Branch.objects.filter(is_active=True)
    )

    def validate(self, data):
        if User.objects.filter(username__iexact=data["username"]).exists():
            raise serializers.ValidationError("Бұл логин бар")
        try:
            validate_password(data["password"], User(username=data["username"]))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return data


class StaffStatusInput(serializers.Serializer):
    is_active = serializers.BooleanField()


class BranchInput(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=200, allow_blank=True, default="")
