from django.db import models
import uuid


class Unit(models.Model):
    """Unit of measurement for items."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Unit'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class State(models.Model):
    """Indian states with codes for GST."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)  # GST state code
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'State'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Country(models.Model):
    """Countries for address."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO 3166-1 alpha-3
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Address(models.Model):
    """Reusable address model for Party, Transporter, Company, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='addresses')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='addresses', default=1)  # Default India
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Address'
        ordering = ['city', 'address_line_1']

    def __str__(self):
        return f"{self.address_line_1}, {self.city}, {self.state.name}"

    @property
    def full_address(self):
        """Return full formatted address."""
        lines = [self.address_line_1]
        if self.address_line_2:
            lines.append(self.address_line_2)
        if self.landmark:
            lines.append(f"Landmark: {self.landmark}")
        lines.append(f"{self.city}, {self.district + ', ' if self.district else ''}{self.state.name} - {self.pincode}")
        lines.append(self.country.name)
        return "\n".join(lines)


class Party(models.Model):
    """Customer/Vendor master - company neutral, linked through sales."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    party_code = models.CharField(max_length=50, unique=True)
    party_name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=15)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='parties')
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
        verbose_name = 'Party'
        ordering = ['party_name']

    def __str__(self):
        return f"{self.party_name} ({self.party_code})"

    @property
    def state(self):
        """Get state from address."""
        return self.address.state.name if self.address else ''

    @property
    def state_code(self):
        """Get state code from address."""
        return self.address.state.code if self.address else ''


class Item(models.Model):
    """Product/Item master - company neutral, linked through sales."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_code = models.CharField(max_length=50, unique=True)
    item_name = models.CharField(max_length=255)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='items')
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
    """Transporter master - company neutral, linked through vehicle/sales."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    gstin = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=20)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='transporters')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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


class LoadingPoint(models.Model):
    """Loading points within the factory premises."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Loading Point'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
