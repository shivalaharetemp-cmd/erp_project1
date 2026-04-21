from django.db import models
import uuid


class Party(models.Model):
    """Customer/Vendor master."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='parties')
    party_code = models.CharField(max_length=50)
    party_name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=15)
    state = models.CharField(max_length=100)
    state_code = models.CharField(max_length=2)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    party_type = models.CharField(max_length=10, choices=[
        ('Customer', 'Customer'),
        ('Vendor', 'Vendor'),
        ('Both', 'Both'),
    ], default='Customer')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_terms = models.IntegerField(default=30)  # days
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'party_code')
        verbose_name = 'Party'
        ordering = ['party_name']

    def __str__(self):
        return f"{self.party_name} ({self.party_code})"


class Item(models.Model):
    """Product/Item master with tax configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=50, unique=True)
    item_name = models.CharField(max_length=255)
    unit = models.CharField(max_length=10, choices=[
        ('MT', 'Metric Tonne'),
        ('KG', 'Kilogram'),
        ('LTR', 'Litre'),
        ('PCS', 'Pieces'),
    ], default='MT')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    hsn_code = models.CharField(max_length=8)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item'
        ordering = ['item_name']

    def __str__(self):
        return f"{self.item_name} ({self.item_code})"


class Transporter(models.Model):
    """Transporter master."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='transporters')
    name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'name')
        verbose_name = 'Transporter'
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    """Purchase order with item lines."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='purchase_orders')
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name='purchase_orders')
    po_number = models.CharField(max_length=100)
    po_date = models.DateField()
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('Draft', 'Draft'),
        ('Confirmed', 'Confirmed'),
        ('Partially Fulfilled', 'Partially Fulfilled'),
        ('Fulfilled', 'Fulfilled'),
        ('Cancelled', 'Cancelled'),
    ], default='Draft')
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_pos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'po_number')
        verbose_name = 'Purchase Order'
        ordering = ['-po_date']

    def __str__(self):
        return f"PO-{self.po_number}"


class PurchaseOrderItem(models.Model):
    """Individual line items in a purchase order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='po_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    fulfilled_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    class Meta:
        unique_together = ('purchase_order', 'item')
        verbose_name = 'PO Item'

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.item.item_name}"
