from django.db import models
import uuid


class InvoiceNumberSequence(models.Model):
    """Maintains invoice numbering sequence per company per financial year."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='invoice_sequences')
    financial_year = models.CharField(max_length=10)  # e.g., '2024-25'
    last_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ('company', 'financial_year')

    def __str__(self):
        return f"{self.company.code}/{self.financial_year}: {self.last_number}"


class CreditNoteNumberSequence(models.Model):
    """Maintains credit note numbering sequence per company per financial year."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='cn_sequences')
    financial_year = models.CharField(max_length=10)
    last_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ('company', 'financial_year')

    def __str__(self):
        return f"CN-{self.company.code}/{self.financial_year}: {self.last_number}"


class Sale(models.Model):
    """Sales invoice created from vehicle."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.OneToOneField('vehicles.Vehicle', on_delete=models.PROTECT, related_name='sale')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='sales')
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, related_name='sales')

    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField(auto_now_add=True)
    financial_year = models.CharField(max_length=10)

    # Totals (frozen at creation)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Cancelled', 'Cancelled'),
    ], default='Active')

    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_sales')
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Sale'
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.party.party_name}"


class SaleItem(models.Model):
    """Individual line items in a sale."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='sale_items')
    vehicle_item = models.ForeignKey(
        'vehicles.VehicleItem', on_delete=models.PROTECT, related_name='sale_items'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Tax frozen at invoice creation
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_type = models.CharField(max_length=20)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    hsn_code = models.CharField(max_length=8)

    class Meta:
        verbose_name = 'Sale Item'

    def __str__(self):
        return f"{self.sale.invoice_number} - {self.item.item_name}"


class CreditNote(models.Model):
    """Credit note for reversing a sale."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.OneToOneField(Sale, on_delete=models.PROTECT, related_name='credit_note')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.PROTECT, related_name='credit_notes')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='credit_notes')
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, related_name='credit_notes')

    credit_note_number = models.CharField(max_length=100, unique=True)
    credit_note_date = models.DateField(auto_now_add=True)
    financial_year = models.CharField(max_length=10)

    # Totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Cancelled', 'Cancelled'),
    ], default='Active')

    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_credit_notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Credit Note'
        ordering = ['-credit_note_date']

    def __str__(self):
        return f"{self.credit_note_number} - {self.party.party_name}"


class CreditNoteItem(models.Model):
    """Individual line items in a credit note."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT, related_name='credit_note_items')
    item = models.ForeignKey('masters.Item', on_delete=models.PROTECT, related_name='credit_note_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_type = models.CharField(max_length=20)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    hsn_code = models.CharField(max_length=8)

    class Meta:
        verbose_name = 'Credit Note Item'

    def __str__(self):
        return f"{self.credit_note.credit_note_number} - {self.item.item_name}"
