import secrets, uuid
from concurrent.futures import ThreadPoolExecutor
from django.db import connections, connection, DatabaseError, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from core.models import Branch, User, Card, Operation
from core.services import token_hash, record_operation
from core.exceptions import BusinessError


class Fixtures:
    def make_fixtures(self):
        self.branch = Branch.objects.create(name="Ақсай")
        self.other_branch = Branch.objects.create(name="Орталық")
        self.manager = User.objects.create_user(
            username="owner",
            password="Local-test-password-321",
            role="manager",
            branch=self.branch,
        )
        self.cashier = User.objects.create_user(
            username="cashier",
            password="Local-test-password-321",
            role="cashier",
            branch=self.branch,
        )
        self.other = User.objects.create_user(
            username="cashier2",
            password="Local-test-password-321",
            role="cashier",
            branch=self.other_branch,
        )
        self.token = secrets.token_urlsafe(32)
        self.card = Card.objects.create(token_hash=token_hash(self.token))

    def op(self, kind="purchase", quantity=1, **kw):
        return record_operation(
            actor=kw.pop("actor", self.cashier),
            card_id=self.card.pk,
            kind=kind,
            quantity=quantity,
            request_key=kw.pop("request_key", uuid.uuid4()),
            **kw,
        )


class LoyaltyTests(Fixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_five_plus_four_yields_reward_and_two_stamps(self):
        self.op(quantity=5)
        self.op(quantity=4)
        self.card.refresh_from_db()
        self.assertEqual((self.card.stamps, self.card.rewards), (2, 1))

    def test_bulk_purchase_can_unlock_multiple_rewards(self):
        self.op(quantity=100)
        self.card.refresh_from_db()
        self.assertEqual((self.card.stamps, self.card.rewards), (2, 14))

    def test_reward_does_not_add_paid_stamps_and_cannot_be_reused(self):
        self.op(quantity=7)
        self.op(kind="redeem")
        self.card.refresh_from_db()
        self.assertEqual(
            (self.card.paid_units, self.card.redeemed_units, self.card.rewards),
            (7, 1, 0),
        )
        with self.assertRaises(BusinessError):
            self.op(kind="redeem")
        self.assertEqual(Operation.objects.count(), 2)

    def test_purchase_idempotency(self):
        key = uuid.uuid4()
        a = self.op(quantity=3, request_key=key)
        b = self.op(quantity=3, request_key=key)
        self.assertEqual(a.id, b.id)
        self.card.refresh_from_db()
        self.assertEqual(self.card.paid_units, 3)

    def test_retry_of_redeem_returns_original_even_if_reward_gone(self):
        self.op(quantity=7)
        key = uuid.uuid4()
        a = self.op(kind="redeem", request_key=key)
        b = self.op(kind="redeem", request_key=key)
        self.assertEqual(a.id, b.id)

    def test_key_cannot_be_reused_with_different_payload(self):
        key = uuid.uuid4()
        self.op(quantity=3, request_key=key)
        with self.assertRaises(BusinessError):
            self.op(quantity=4, request_key=key)

    def test_key_cannot_be_reused_by_another_actor(self):
        key = uuid.uuid4()
        self.op(request_key=key)
        with self.assertRaises(BusinessError):
            self.op(request_key=key, actor=self.other)

    def test_manager_reversal_is_append_only(self):
        op = self.op(quantity=7)
        rev = self.op(
            kind="reversal",
            quantity=7,
            actor=self.manager,
            reverses=op.id,
            reason="Қате енгізілген шай",
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.paid_units, 0)
        self.assertEqual(Operation.objects.count(), 2)
        self.assertEqual(rev.reverses_id, op.id)
        with self.assertRaises(BusinessError):
            self.op(
                kind="reversal",
                quantity=7,
                actor=self.manager,
                reverses=op.id,
                reason="Қайта қайтару",
            )

    def test_cannot_reverse_spent_reward_purchase_until_redemption_reversed(self):
        purchase = self.op(quantity=7)
        reward = self.op(kind="redeem")
        with self.assertRaises(BusinessError):
            self.op(
                kind="reversal",
                quantity=7,
                actor=self.manager,
                reverses=purchase.id,
                reason="Шай саны қате",
            )
        self.op(
            kind="reversal",
            actor=self.manager,
            reverses=reward.id,
            reason="Сыйлық берілмеді",
        )
        self.op(
            kind="reversal",
            quantity=7,
            actor=self.manager,
            reverses=purchase.id,
            reason="Шай саны қате",
        )
        self.card.refresh_from_db()
        self.assertEqual((self.card.paid_units, self.card.redeemed_units), (0, 0))

    def test_cashier_cannot_reverse(self):
        op = self.op()
        with self.assertRaises(BusinessError):
            self.op(kind="reversal", reverses=op.id, reason="Қате енгізілді")

    def test_disabled_cashier_cannot_write(self):
        self.cashier.is_active = False
        self.cashier.save()
        with self.assertRaises(BusinessError):
            self.op()

    def test_inactive_branch_cannot_write(self):
        self.branch.is_active = False
        self.branch.save()
        with self.assertRaises(BusinessError):
            self.op()

    def test_negative_and_bool_quantities_rejected(self):
        for quantity in [-1, 0, 101, True]:
            with self.assertRaises(BusinessError):
                self.op(quantity=quantity)
        self.assertEqual(Operation.objects.count(), 0)

    def test_database_prevents_mutating_audit_records(self):
        op = self.op()
        with self.assertRaises(DatabaseError), transaction.atomic():
            Operation.objects.filter(pk=op.pk).update(quantity=2, paid_delta=2)
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as c:
                c.execute("DELETE FROM core_operation WHERE id=%s", [op.id])
        self.assertEqual(Operation.objects.count(), 1)


@override_settings(SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class ApiTests(Fixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.client = APIClient()

    def test_guest_card_create_is_idempotent_and_empty(self):
        token = secrets.token_urlsafe(32)
        a = self.client.post("/api/cards/", {"token": token}, format="json")
        b = self.client.post("/api/cards/", {"token": token}, format="json")
        self.assertEqual((a.status_code, b.status_code), (201, 200))
        self.assertEqual(a.data["id"], b.data["id"])
        self.assertEqual(a.data["paid_units"], 0)
        self.assertFalse(Card.objects.filter(token_hash=token).exists())

    def test_same_secret_recovers_card_on_another_client(self):
        self.op(quantity=5)
        a = self.client.get(
            "/api/cards/current/", HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )
        b = APIClient().get(
            "/api/cards/current/", HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )
        self.assertEqual(a.data, b.data)
        self.assertEqual(a.data["stamps"], 5)

    def test_unknown_or_missing_secret_cannot_read_card(self):
        self.assertEqual(self.client.get("/api/cards/current/").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/api/cards/current/",
                HTTP_AUTHORIZATION=f"Bearer {secrets.token_urlsafe(32)}",
            ).status_code,
            404,
        )

    def test_guest_cannot_mutate_or_read_staff_data(self):
        for endpoint in [
            "staff/purchase/",
            "staff/redeem/",
            "staff/lookup/",
            "manager/staff/",
            "manager/branches/",
        ]:
            self.assertEqual(
                self.client.post("/api/" + endpoint, {}, format="json").status_code, 403
            )
        self.assertEqual(self.client.get("/api/staff/operations/").status_code, 403)

    def test_cashier_cannot_access_manager_routes_or_delete(self):
        self.client.force_authenticate(self.cashier)
        op = self.op()
        self.assertEqual(self.client.get("/api/manager/staff/").status_code, 403)
        self.assertEqual(
            self.client.post(
                f"/api/manager/operations/{op.id}/reverse/",
                {"reason": "Қате енгізілді", "request_key": str(uuid.uuid4())},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(self.client.delete("/api/staff/operations/").status_code, 405)

    def test_cashier_history_is_branch_scoped(self):
        self.op()
        self.op(actor=self.other)
        self.client.force_authenticate(self.cashier)
        data = self.client.get("/api/staff/operations/").data
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["branch"], self.branch.name)

    def test_history_is_paginated_without_per_row_queries(self):
        for _ in range(26):
            self.op()
        with self.assertNumQueries(2):
            response = self.client.get(
                "/api/cards/history/", HTTP_AUTHORIZATION=f"Bearer {self.token}"
            )
        self.assertEqual(len(response.data["items"]), 25)
        self.assertTrue(response.data["has_more"])
        response = self.client.get(
            "/api/cards/history/?page=2", HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )
        self.assertEqual(len(response.data["items"]), 1)
        self.assertFalse(response.data["has_more"])

    def test_guest_history_omits_internal_actor_and_reason(self):
        self.op()
        data = self.client.get(
            "/api/cards/history/", HTTP_AUTHORIZATION=f"Bearer {self.token}"
        ).data
        self.assertNotIn("actor", data["items"][0])
        self.assertNotIn("reason", data["items"][0])

    def test_login_requires_csrf_and_session_writes_require_csrf(self):
        c = APIClient(enforce_csrf_checks=True)
        self.assertEqual(
            c.post(
                "/api/auth/login/",
                {"username": "owner", "password": "Local-test-password-321"},
                format="json",
            ).status_code,
            403,
        )
        token = c.get("/api/auth/csrf/").json()["csrfToken"]
        response = c.post(
            "/api/auth/login/",
            {"username": "owner", "password": "Local-test-password-321"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            c.post(
                "/api/staff/purchase/",
                {
                    "card_id": str(self.card.id),
                    "quantity": 1,
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            ).status_code,
            403,
        )
        fresh = c.get("/api/auth/csrf/").json()["csrfToken"]
        response = c.post(
            "/api/staff/purchase/",
            {
                "card_id": str(self.card.id),
                "quantity": 1,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
            HTTP_X_CSRFTOKEN=fresh,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_limits_failed_attempts(self):
        for _ in range(8):
            self.assertEqual(
                self.client.post(
                    "/api/auth/login/",
                    {"username": "owner", "password": "wrong"},
                    format="json",
                ).status_code,
                400,
            )
        self.assertEqual(
            self.client.post(
                "/api/auth/login/",
                {"username": "owner", "password": "Local-test-password-321"},
                format="json",
            ).status_code,
            429,
        )

    def test_manager_creates_and_disables_staff(self):
        self.client.force_authenticate(self.manager)
        data = {
            "username": "new.cashier",
            "name": "Кассир",
            "password": "Strong-new-password-741",
            "role": "cashier",
            "branch_id": str(self.branch.id),
        }
        r = self.client.post("/api/manager/staff/", data, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.data)
        r = self.client.patch(
            f"/api/manager/staff/{r.data['id']}/", {"is_active": False}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["is_active"])

    def test_manager_cannot_disable_self(self):
        self.client.force_authenticate(self.manager)
        self.assertEqual(
            self.client.patch(
                f"/api/manager/staff/{self.manager.id}/",
                {"is_active": False},
                format="json",
            ).status_code,
            400,
        )


class ConcurrentTests(Fixtures, TransactionTestCase):
    def setUp(self):
        self.make_fixtures()

    def worker(self, kind, actor_id, key, quantity=1):
        connections.close_all()
        try:
            actor = User.objects.get(pk=actor_id)
            result = record_operation(
                actor=actor,
                card_id=self.card.id,
                kind=kind,
                quantity=quantity,
                request_key=key,
            )
            return str(result.id)
        except BusinessError:
            return "conflict"
        finally:
            connections.close_all()

    def test_two_cashiers_redeem_only_once(self):
        self.op(quantity=7)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(
                pool.map(
                    lambda args: self.worker(*args),
                    [
                        ("redeem", self.cashier.id, uuid.uuid4()),
                        ("redeem", self.other.id, uuid.uuid4()),
                    ],
                )
            )
        self.assertEqual(result.count("conflict"), 1)
        self.card.refresh_from_db()
        self.assertEqual(self.card.redeemed_units, 1)

    def test_repeated_purchase_requests_count_once(self):
        key = uuid.uuid4()
        with ThreadPoolExecutor(max_workers=5) as pool:
            result = list(
                pool.map(
                    lambda _: self.worker("purchase", self.cashier.id, key, 3), range(5)
                )
            )
        self.assertEqual(len(set(result)), 1)
        self.card.refresh_from_db()
        self.assertEqual(self.card.paid_units, 3)

    def test_concurrent_independent_purchases_are_not_lost(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(
                pool.map(
                    lambda i: self.worker(
                        "purchase",
                        self.cashier.id if i % 2 else self.other.id,
                        uuid.uuid4(),
                        2,
                    ),
                    range(8),
                )
            )
        self.card.refresh_from_db()
        self.assertEqual(
            (self.card.paid_units, self.card.stamps, self.card.rewards), (16, 2, 2)
        )

    def test_same_key_on_two_cards_rolls_back_losing_balance(self):
        other_card = Card.objects.create(
            token_hash=token_hash(secrets.token_urlsafe(32))
        )
        key = uuid.uuid4()

        def write(args):
            actor_id, card_id = args
            connections.close_all()
            try:
                record_operation(
                    actor=User.objects.get(pk=actor_id),
                    card_id=card_id,
                    kind="purchase",
                    quantity=4,
                    request_key=key,
                )
                return "ok"
            except BusinessError:
                return "conflict"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(
                pool.map(
                    write,
                    [(self.cashier.pk, self.card.pk), (self.other.pk, other_card.pk)],
                )
            )
        self.card.refresh_from_db()
        other_card.refresh_from_db()
        self.assertEqual(sorted(result), ["conflict", "ok"])
        self.assertEqual(self.card.paid_units + other_card.paid_units, 4)
        self.assertEqual(Operation.objects.count(), 1)
