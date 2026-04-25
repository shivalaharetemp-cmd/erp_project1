from django.contrib import admin
from .models import (
    LedgerAccount, LedgerEntry, AccountReceivable, AccountPayable,
    Receipt, Payment, TransporterBill, TransporterBillPayment
)


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'account_type', 'current_balance', 'is_active']
    list_filter = ['account_type', 'company', 'is_active']
    search_fields = ['code', 'name']


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'voucher_type', 'account', 'entry_date', 'debit', 'credit']
    list_filter = ['voucher_type', 'company', 'entry_date']
    search_fields = ['voucher_number', 'narration']
    date_hierarchy = 'entry_date'


@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'party', 'company', 'total_amount', 'balance_amount', 'status', 'due_date']
    list_filter = ['status', 'company']
    search_fields = ['invoice_number', 'party__party_name']
    date_hierarchy = 'invoice_date'


@admin.register(AccountPayable)
class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'payable_type', 'company', 'total_amount', 'balance_amount', 'status', 'due_date']
    list_filter = ['payable_type', 'status', 'company']
    search_fields = ['bill_number']
    date_hierarchy = 'bill_date'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receivable', 'receipt_date', 'amount', 'payment_mode']
    list_filter = ['payment_mode', 'company']
    date_hierarchy = 'receipt_date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payable', 'payment_date', 'amount', 'payment_mode']
    list_filter = ['payment_mode', 'company']
    date_hierarchy = 'payment_date'


@admin.register(TransporterBill)
class TransporterBillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'transporter', 'company', 'total_amount', 'status', 'bill_date']
    list_filter = ['status', 'company']
    search_fields = ['bill_number', 'transporter__name']
    filter_horizontal = ['freights']


@admin.register(TransporterBillPayment)
class TransporterBillPaymentAdmin(admin.ModelAdmin):
    list_display = ['transporter_bill', 'payment_date', 'amount', 'payment_mode']
    list_filter = ['payment_mode']
