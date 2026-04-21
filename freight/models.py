from django.db import models
import uuid


class Freight(models.Model):
    """Original freight entry linked to vehicle."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='freights')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='freights')

    FREIGHT_TYPE_CHOICES = [
        ('PerQuantity', 'Per Quantity'),
        ('Fixed', 'Fixed'),
        ('Guaranteed', 'Guaranteed'),
    ]
    freight_type = models.CharField(max_length=20, choices=FREIGHT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_freights')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Freight'
        ordering = ['-created_at']

    def __str__(self):
        return f"Freight ({self.freight_type}) - {self.amount} for {self.vehicle.vehicle_number}"

    def calculate_amount(self):
        """Calculate amount based on freight type."""
        if self.freight_type == 'PerQuantity' or self.freight_type == 'Guaranteed':
            if self.quantity and self.rate:
                return self.quantity * self.rate
        return self.amount  # Fixed type


class ReturnFreight(models.Model):
    """Return freight linked to credit note."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='return_freights')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='return_freights')
    credit_note = models.ForeignKey(
        'sales.CreditNote', on_delete=models.PROTECT, related_name='return_freights'
    )

    FREIGHT_TYPE_CHOICES = [
        ('PerQuantity', 'Per Quantity'),
        ('Fixed', 'Fixed'),
        ('Guaranteed', 'Guaranteed'),
    ]
    freight_type = models.CharField(max_length=20, choices=FREIGHT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_return_freights')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Return Freight'
        ordering = ['-created_at']

    def __str__(self):
        return f"Return Freight - {self.amount} for {self.vehicle.vehicle_number}"
