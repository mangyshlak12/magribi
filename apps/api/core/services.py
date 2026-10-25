import hashlib, re
from uuid import UUID
from django.db import transaction, IntegrityError
from django.db.models import F
from .models import Card, Operation, User
from .exceptions import BusinessError


def token_hash(token):
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise BusinessError("Карта сілтемесі жарамсыз", 400)
    return hashlib.sha256(token.encode()).hexdigest()


def operation_result(op):
    return {
        "id": str(op.id),
        "card_id": str(op.card_id),
        "kind": op.kind,
        "quantity": op.quantity,
        "paid_delta": op.paid_delta,
        "redeemed_delta": op.redeemed_delta,
        "actor": op.actor.username,
        "branch": op.branch.name,
        "reason": op.reason,
        "reverses": str(op.reverses_id) if op.reverses_id else None,
        "reversed": op.has_reversal
        if hasattr(op, "has_reversal")
        else Operation.objects.filter(reverses_id=op.id).exists(),
        "created_at": op.created_at.isoformat(),
    }


def card_result(card, staff=False):
    result = {
        "id": str(card.id),
        "stamps": card.stamps,
        "rewards": card.rewards,
        "paid_units": card.paid_units,
        "redeemed_units": card.redeemed_units,
    }
    if staff:
        result["created_at"] = card.created_at.isoformat()
    return result


def same_request(op, actor, card_id, kind, quantity, reverses, reason):
    if not (
        op.actor_id == actor.id
        and str(op.card_id) == str(card_id)
        and op.kind == kind
        and op.quantity == quantity
        and str(op.reverses_id or "") == str(reverses or "")
        and op.reason == reason
    ):
        raise BusinessError("Сұраныс кілті басқа операцияда қолданылған")
    return op


def record_operation(
    *, actor, card_id, kind, quantity, request_key, reverses=None, reason=""
):
    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or not 1 <= quantity <= 100
    ):
        raise BusinessError("Шай саны 1–100 аралығында болсын", 400)
    request_key = UUID(str(request_key))
    try:
        with transaction.atomic():
            actor = (
                User.objects.select_for_update(of=("self",))
                .select_related("branch")
                .get(pk=actor.pk)
            )
            if not actor.is_active or actor.role not in ("manager", "cashier"):
                raise BusinessError("Бұл әрекетке рұқсат жоқ", 403)
            if kind == "reversal" and actor.role != "manager":
                raise BusinessError("Тек басқарушы кері қайтара алады", 403)
            card = Card.objects.select_for_update().get(pk=card_id)
            prior = Operation.objects.filter(request_key=request_key).first()
            if prior:
                return same_request(
                    prior, actor, card_id, kind, quantity, reverses, reason
                )
            original = None
            if kind == "purchase":
                paid, redeemed = quantity, 0
            elif kind == "redeem":
                if quantity != 1:
                    raise BusinessError("Бір сыйлықтан беріңіз", 400)
                if card.rewards < 1:
                    raise BusinessError("Дайын сыйлық жоқ немесе қолданылған")
                paid, redeemed = 0, 1
            elif kind == "reversal":
                reason = reason.strip()
                if len(reason) < 5:
                    raise BusinessError("Себебін жазыңыз (кемінде 5 таңба)", 400)
                original = Operation.objects.select_related("branch").get(
                    pk=reverses, card=card
                )
                if original.kind == "reversal":
                    raise BusinessError("Кері қайтаруды қайта өзгертуге болмайды")
                if original.quantity != quantity:
                    raise BusinessError("Операция саны сәйкес емес", 400)
                if Operation.objects.filter(reverses=original).exists():
                    raise BusinessError("Операция бұрын кері қайтарылған")
                paid, redeemed = -original.paid_delta, -original.redeemed_delta
            else:
                raise BusinessError("Операция түрі жарамсыз", 400)
            if (
                card.paid_units + paid < 0
                or card.redeemed_units + redeemed < 0
                or (card.paid_units + paid) // 7 < card.redeemed_units + redeemed
            ):
                raise BusinessError(
                    "Бұл сатып алудың сыйлығы қолданылған. Алдымен сыйлық беру операциясын кері қайтарыңыз"
                )
            branch = original.branch if original else actor.branch
            if not branch or not branch.is_active:
                raise BusinessError("Белсенді филиалды қызметкерге тағайындаңыз", 400)
            Card.objects.filter(pk=card.pk).update(
                paid_units=F("paid_units") + paid,
                redeemed_units=F("redeemed_units") + redeemed,
            )
            return Operation.objects.create(
                card=card,
                actor=actor,
                branch=branch,
                kind=kind,
                quantity=quantity,
                paid_delta=paid,
                redeemed_delta=redeemed,
                request_key=request_key,
                reason=reason,
                reverses=original,
            )
    except IntegrityError:
        prior = Operation.objects.filter(request_key=request_key).first()
        if prior:
            return same_request(prior, actor, card_id, kind, quantity, reverses, reason)
        raise BusinessError("Операция қатар өзгертілді. Картаны жаңартып көріңіз")
