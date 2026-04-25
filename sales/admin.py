from django.contrib import admin
from .models import (
    Sale, SaleItem, CreditNote, CreditNoteItem,
    InvoiceNumberSequence, CreditNoteNumberSequence,
)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    raw_id_fields = ['item', 'vehicle_item']
    readonly_fields = ['tax_rate', 'tax_type', 'cgst_amount', 'sgst_amount', 'igst_amount', 'hsn_code']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'invoice_date', 'party', 'vehicle', 'subtotal', 'total_tax', 'grand_total', 'status', 'financial_year']
    list_filter = ['status', 'financial_year']
    search_fields = ['invoice_number', 'party__party_name', 'vehicle__vehicle_number']
    raw_id_fields = ['vehicle', 'party', 'created_by', 'company']
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'item', 'quantity', 'rate', 'amount', 'tax_rate']
    raw_id_fields = ['sale', 'item', 'vehicle_item']


class CreditNoteItemInline(admin.TabularInline):
    model = CreditNoteItem
    extra = 0
    raw_id_fields = ['credit_note', 'sale_item', 'item']


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ['credit_note_number', 'credit_note_date', 'party', 'sale', 'grand_total', 'status', 'financial_year']
    list_filter = ['status', 'financial_year']
    search_fields = ['credit_note_number', 'party__party_name', 'sale__invoice_number']
    raw_id_fields = ['sale', 'vehicle', 'party', 'created_by', 'company']
    inlines = [CreditNoteItemInline]


@admin.register(InvoiceNumberSequence)
class InvoiceNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ['company', 'financial_year', 'last_number']


@admin.register(CreditNoteNumberSequence)
class CreditNoteNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ['company', 'financial_year', 'last_number']
