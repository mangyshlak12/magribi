import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "manager", "Басқарушы"
        CASHIER = "cashier", "Кассир"

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.CASHIER)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("username"), name="user_username_case_unique"
            )
        ]


class Card(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True)
    paid_units = models.PositiveIntegerField(default=0)
    redeemed_units = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def stamps(self):
        return self.paid_units % 7

    @property
    def rewards(self):
        return self.paid_units // 7 - self.redeemed_units

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(paid_units__gte=F("redeemed_units") * 7),
                name="card_rewards_never_negative",
            )
        ]


class Operation(models.Model):
    class Kind(models.TextChoices):
        PURCHASE = "purchase", "Сатып алу"
        REDEEM = "redeem", "Сыйлық беру"
        REVERSAL = "reversal", "Кері қайтару"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(Card, on_delete=models.PROTECT, related_name="operations")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    quantity = models.PositiveSmallIntegerField()
    paid_delta = models.SmallIntegerField(default=0)
    redeemed_delta = models.SmallIntegerField(default=0)
    request_key = models.UUIDField(unique=True)
    reason = models.CharField(max_length=500, blank=True)
    reverses = models.OneToOneField(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="reversal"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["card", "-created_at"]),
            models.Index(fields=["branch", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1, quantity__lte=100),
                name="operation_quantity_range",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        kind="purchase",
                        paid_delta=F("quantity"),
                        redeemed_delta=0,
                        reverses__isnull=True,
                    )
                    | Q(
                        kind="redeem",
                        paid_delta=0,
                        redeemed_delta=1,
                        quantity=1,
                        reverses__isnull=True,
                    )
                    | (Q(kind="reversal", reverses__isnull=False) & ~Q(reason=""))
                ),
                name="operation_shape",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Operations are immutable; create a reversal")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Operations cannot be deleted")


class LoginFailure(models.Model):
    username_hash = models.CharField(max_length=64, db_index=True)
    ip_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
