import json
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Customer, MilkEntry, OfflineMutation, Payment


class OfflineSyncTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="offline-test", password="test-password")
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(name="Offline customer", balance_amount="100.00")

    def post_mutation(self, mutation_id, action, data):
        return self.client.post(
            "/accounts/offline/sync/",
            data=json.dumps({
                "mutation_id": str(mutation_id),
                "action": action,
                "data": data,
            }),
            content_type="application/json",
        )

    def test_payment_mutation_is_idempotent_and_updates_balance_once(self):
        mutation_id = uuid.uuid4()
        payload = {
            "customer_id": self.customer.pk,
            "amount": "10.00",
            "paid_on": "2026-11-22",
            "note": "cash",
            "local_id": "local-payment-1",
        }

        first = self.post_mutation(mutation_id, "payment.create", payload)
        second = self.post_mutation(mutation_id, "payment.create", payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Payment.objects.filter(customer=self.customer).count(), 1)
        self.customer.refresh_from_db()
        self.assertEqual(str(self.customer.balance_amount), "90.00")
        self.assertEqual(OfflineMutation.objects.filter(user=self.user).count(), 1)

    def test_stale_customer_update_is_rejected(self):
        previous_version = self.customer.updated_at.isoformat()
        Customer.objects.filter(pk=self.customer.pk).update(
            name="Changed while offline",
            updated_at=timezone.now() + timedelta(seconds=5),
        )

        response = self.post_mutation(
            uuid.uuid4(),
            "customer.update",
            {
                "id": self.customer.pk,
                "name": "Offline edit",
                "balance_amount": "100.00",
                "expected_updated_at": previous_version,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Changed while offline")

    def test_offline_snapshot_and_shell_are_available_to_signed_in_user(self):
        MilkEntry.objects.create(
            customer=self.customer,
            date="2026-11-22",
            quantity_ml=1500,
        )

        shell = self.client.get("/accounts/offline/")
        snapshot = self.client.get("/accounts/offline/data/")

        self.assertEqual(shell.status_code, 200)
        self.assertContains(shell, "Offline workspace")
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual(snapshot.json()["customers"][0]["id"], self.customer.pk)
        self.assertEqual(snapshot.json()["entries"][0]["quantity_ml"], 1500)

