from django.db import models
import uuid


class Stock(models.Model):
    """Current stock position per company per item."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='stocks')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='stocks')
    quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0, help_text='Quantity reserved for pending dispatches')
    
    class Meta:
        unique_together = ('company', 'item')
        verbose_name = 'Stock'
        ordering = ['item__item_name']

    def __str__(self):
        return f"{self.item.item_name} - {self.quantity} {self.item.unit} ({self.company.code})"

    @property
    def available_quantity(self):
        """Available = Total - Reserved"""
        return self.quantity - self.reserved_quantity


class StockMovement(models.Model):
    """Inventory movement transactions - IN and OUT."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='stock_movements')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='stock_movements')
    
    MOVEMENT_TYPE_CHOICES = [
        ('IN_PURCHASE', 'Purchase Receipt'),
        ('IN_RETURN', 'Sale Return'),
        ('IN_ADJUSTMENT', 'Stock Adjustment (+)'),
        ('OUT_SALE', 'Sale Dispatch'),
        ('OUT_CONSUMPTION', 'Internal Consumption'),
        ('OUT_ADJUSTMENT', 'Stock Adjustment (-)'),
        ('OUT_TRANSFER', 'Inter-Company Transfer'),
    ]
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    reference_no = models.CharField(max_length=100, blank=True)
    reference_date = models.DateField(null=True, blank=True)
    
    # Links to related documents
    purchase_order = models.ForeignKey('masters.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Stock Movement'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.movement_type} - {self.item.item_name} ({self.quantity})"


class StockAdjustment(models.Model):
    """Stock adjustment for physical count corrections, damages, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='stock_adjustments')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='stock_adjustments')
    
    ADJUSTMENT_TYPE_CHOICES = [
        ('Physical_Count', 'Physical Count Correction'),
        ('Damage', 'Damaged Goods'),
        ('Expired', 'Expired Goods'),
        ('Theft', 'Theft/Loss'),
        ('Other', 'Other'),
    ]
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    
    old_quantity = models.DecimalField(max_digits=15, decimal_places=3)
    new_quantity = models.DecimalField(max_digits=15, decimal_places=3)
    difference = models.DecimalField(max_digits=15, decimal_places=3)
    
    reason = models.TextField()
    approved_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='approved_adjustments', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_adjustments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Stock Adjustment'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.adjustment_type} - {self.item.item_name} ({self.difference})"
