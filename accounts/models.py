from django.db import models
import uuid
from decimal import Decimal


class LedgerAccount(models.Model):
    """Chart of accounts for each company."""
    ACCOUNT_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='ledger_accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ('company', 'code')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.company.code})"


class LedgerEntry(models.Model):
    """Individual accounting entries (double-entry bookkeeping)."""
    ENTRY_TYPES = [
        ('SALE', 'Sale Invoice'),
        ('SALE_RETURN', 'Sale Return/Credit Note'),
        ('PURCHASE', 'Purchase'),
        ('PAYMENT', 'Payment'),
        ('RECEIPT', 'Receipt'),
        ('FREIGHT', 'Freight'),
        ('JOURNAL', 'Journal Voucher'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='ledger_entries')
    entry_date = models.DateField()
    voucher_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    voucher_number = models.CharField(max_length=100)
    
    # Links to source documents
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True)
    credit_note = models.ForeignKey('sales.CreditNote', on_delete=models.SET_NULL, null=True, blank=True)
    freight = models.ForeignKey('freight.Freight', on_delete=models.SET_NULL, null=True, blank=True)
    
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name='entries')
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, null=True, blank=True)
    
    # Double-entry amounts
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    narration = models.TextField(blank=True)
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-entry_date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.account.name}"


class AccountReceivable(models.Model):
    """Track money owed by customers (from sales)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='receivables')
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, related_name='receivables')
    
    # Source document
    sale = models.OneToOneField('sales.Sale', on_delete=models.CASCADE, related_name='receivable')
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    # Amount tracking
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"AR-{self.invoice_number} - {self.party.party_name} - {self.balance_amount}"
    
    def update_status(self):
        """Update status based on payments."""
        from django.utils import timezone
        self.balance_amount = self.total_amount - self.paid_amount
        
        if self.balance_amount <= 0:
            self.status = 'PAID'
        elif self.paid_amount > 0:
            self.status = 'PARTIAL'
        elif timezone.now().date() > self.due_date:
            self.status = 'OVERDUE'
        else:
            self.status = 'UNPAID'
        self.save()


class AccountPayable(models.Model):
    """Track money owed to suppliers/transporters."""
    PAYABLE_TYPES = [
        ('TRANSPORTER', 'Transporter Freight'),
        ('SUPPLIER', 'Supplier/Party'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='payables')
    payable_type = models.CharField(max_length=20, choices=PAYABLE_TYPES)
    
    # Party/Transporter
    party = models.ForeignKey('masters.Party', on_delete=models.PROTECT, null=True, blank=True, related_name='payables')
    transporter = models.ForeignKey('masters.Transporter', on_delete=models.PROTECT, null=True, blank=True, related_name='payables')
    
    # Source document
    freight = models.ForeignKey('freight.Freight', on_delete=models.SET_NULL, null=True, blank=True, related_name='payable')
    purchase_order = models.ForeignKey('masters.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='payable')
    
    bill_number = models.CharField(max_length=100, blank=True)
    bill_date = models.DateField()
    due_date = models.DateField()
    
    # Amount tracking
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-bill_date']
    
    def __str__(self):
        party_name = self.party.party_name if self.party else (self.transporter.name if self.transporter else 'Unknown')
        return f"AP-{self.bill_number or 'N/A'} - {party_name} - {self.balance_amount}"
    
    def update_status(self):
        """Update status based on payments."""
        from django.utils import timezone
        self.balance_amount = self.total_amount - self.paid_amount
        
        if self.balance_amount <= 0:
            self.status = 'PAID'
        elif self.paid_amount > 0:
            self.status = 'PARTIAL'
        elif timezone.now().date() > self.due_date:
            self.status = 'OVERDUE'
        else:
            self.status = 'UNPAID'
        self.save()


class Payment(models.Model):
    """Record payments made to parties/suppliers (for payables)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='payments')
    payable = models.ForeignKey(AccountPayable, on_delete=models.PROTECT, related_name='payments')
    
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=50, choices=[
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('UPI', 'UPI'),
        ('NEFT', 'NEFT/RTGS'),
    ])
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"PAY-{self.payment_date} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.payable.update_status()


class Receipt(models.Model):
    """Record receipts from customers (for receivables)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='receipts')
    receivable = models.ForeignKey(AccountReceivable, on_delete=models.PROTECT, related_name='receipts')
    
    receipt_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=50, choices=[
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('UPI', 'UPI'),
        ('NEFT', 'NEFT/RTGS'),
    ])
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-receipt_date']
    
    def __str__(self):
        return f"RCPT-{self.receipt_date} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receivable.update_status()


class TransporterBill(models.Model):
    """Freight bills for transporters with complete tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='transporter_bills')
    transporter = models.ForeignKey('masters.Transporter', on_delete=models.PROTECT, related_name='bills')
    
    bill_number = models.CharField(max_length=100)
    bill_date = models.DateField()
    due_date = models.DateField()
    
    # Link to freights included in this bill
    freights = models.ManyToManyField('freight.Freight', related_name='transporter_bills')
    
    # Amounts
    freight_amount = models.DecimalField(max_digits=15, decimal_places=2)
    extra_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transporter_bills')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='created_transporter_bills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-bill_date']
        unique_together = ('company', 'bill_number')
    
    def __str__(self):
        return f"TB-{self.bill_number} - {self.transporter.name} - {self.total_amount}"
    
    def calculate_total(self):
        """Calculate total amount."""
        self.total_amount = self.freight_amount + self.extra_charges - self.deductions
        self.balance_amount = self.total_amount - self.paid_amount
        return self.total_amount
    
    def update_status(self):
        """Update payment status."""
        from django.utils import timezone
        self.balance_amount = self.total_amount - self.paid_amount
        
        if self.balance_amount <= 0:
            self.status = 'PAID'
        elif self.paid_amount > 0:
            self.status = 'PARTIAL'
        elif self.status == 'APPROVED' and timezone.now().date() > self.due_date:
            self.status = 'OVERDUE'
        self.save()


class TransporterBillPayment(models.Model):
    """Payments made against transporter bills."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transporter_bill = models.ForeignKey(TransporterBill, on_delete=models.CASCADE, related_name='bill_payments')
    
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=50, choices=[
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('UPI', 'UPI'),
        ('NEFT', 'NEFT/RTGS'),
    ])
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"TBP-{self.payment_date} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.transporter_bill.paid_amount = sum(
            bp.amount for bp in self.transporter_bill.bill_payments.all()
        )
        self.transporter_bill.calculate_total()
        self.transporter_bill.update_status()
