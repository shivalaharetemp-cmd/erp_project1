from django.db import models
import uuid


class Vehicle(models.Model):
    """Vehicle placement with complete status lifecycle."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='vehicles', null=True, blank=True)
    vehicle_number = models.CharField(max_length=20)
    transporter = models.ForeignKey(
        'masters.Transporter', on_delete=models.PROTECT, related_name='vehicles'
    )
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, related_name='vehicles')
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Loaded', 'Loaded'),
        ('InTransit', 'InTransit'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_vehicles')
    loaded_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cancelled_vehicles'
    )
    version = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vehicle'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle_number} ({self.status})"

    @property
    def is_editable(self):
        return self.status == 'Pending'

    @property
    def has_invoice(self):
        return hasattr(self, 'sale') and self.sale is not None


class VehicleItem(models.Model):
    """Items loaded onto a vehicle."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='vehicle_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unloaded_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    class Meta:
        unique_together = ('vehicle', 'item')
        verbose_name = 'Vehicle Item'

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.item.item_name} ({self.quantity} {self.item.unit})"


class VehicleChangeLog(models.Model):
    """Audit log for vehicle number changes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='change_logs')
    old_vehicle_number = models.CharField(max_length=20)
    new_vehicle_number = models.CharField(max_length=20)
    changed_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='vehicle_changes')
    reason = models.TextField()
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vehicle Change Log'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.old_vehicle_number} -> {self.new_vehicle_number} by {self.changed_by.username}"
