from django.db import models # pyright: ignore[reportMissingModuleSource]
from django.utils import timezone # pyright: ignore[reportMissingModuleSource]
from django.conf import settings # pyright: ignore[reportMissingModuleSource]
from decimal import Decimal

PRICE_PER_LITRE = getattr(settings, 'PRICE_PER_LITRE', 50.0)

class Customer(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) # pyright: ignore[reportArgumentType]
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name or "Unknown Customer"

    class Meta:
        ordering = ['-created_at']


class MilkEntry(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='milk_entries')
    date = models.DateField(default=timezone.now)
    quantity_ml = models.IntegerField(default=0)  # quantity in ml
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    @property
    def litres(self):
        """Convert ml to litres"""
        return Decimal(self.quantity_ml) / Decimal(1000)

    @property
    def amount(self):
        """Calculate amount based on litres"""
        return self.litres * Decimal(PRICE_PER_LITRE)

    def __str__(self):
        return f"{self.customer.name} - {self.date} - {self.quantity_ml}ml"

    class Meta:
        ordering = ['-date']

# =========================================================
# ADD THIS TO YOUR models.py
# =========================================================
# 1. Add this import at the top if not already present:
#    from django.utils import timezone

# 2. Add this model class to models.py:

class Payment(models.Model):
    customer    = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on     = models.DateField(default=timezone.localdate)
    note        = models.CharField(max_length=255, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-created_at']

    def __str__(self):
        return f"{self.customer.name} – ₹{self.amount} on {self.paid_on}"
