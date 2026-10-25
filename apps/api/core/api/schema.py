"""Published REST response contracts, separate from persistence models."""

from rest_framework import serializers


class CardOutput(serializers.Serializer):
    id = serializers.UUIDField()
    stamps = serializers.IntegerField()
    rewards = serializers.IntegerField()
    paid_units = serializers.IntegerField()
    redeemed_units = serializers.IntegerField()


class StaffOutput(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=["manager", "cashier"])
    is_active = serializers.BooleanField()
    branch_id = serializers.UUIDField(allow_null=True)
    branch = serializers.CharField(allow_null=True)


class BranchOutput(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    address = serializers.CharField()
    is_active = serializers.BooleanField()


class OperationOutput(serializers.Serializer):
    id = serializers.UUIDField()
    card_id = serializers.UUIDField(required=False)
    kind = serializers.ChoiceField(choices=["purchase", "redeem", "reversal"])
    quantity = serializers.IntegerField()
    paid_delta = serializers.IntegerField()
    redeemed_delta = serializers.IntegerField()
    actor = serializers.CharField(required=False)
    branch = serializers.CharField()
    reason = serializers.CharField(required=False)
    reverses = serializers.UUIDField(allow_null=True)
    reversed = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class HistoryOutput(serializers.Serializer):
    items = OperationOutput(many=True)
    page = serializers.IntegerField()
    has_more = serializers.BooleanField()


class MutationOutput(serializers.Serializer):
    ok = serializers.BooleanField()
    operation = OperationOutput()
    card = CardOutput(required=False)


class OkOutput(serializers.Serializer):
    ok = serializers.BooleanField()


class SummaryOutput(serializers.Serializer):
    cards = serializers.IntegerField()
    paid_units = serializers.IntegerField()
    redeemed_units = serializers.IntegerField()
    operations = serializers.IntegerField()
    cashiers = serializers.IntegerField()
