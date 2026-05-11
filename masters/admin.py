from django.contrib import admin
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem, Unit


class POItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    raw_id_fields = ['item']


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['party_name', 'party_code', 'party_type', 'state', 'state_code', 'gstin', 'is_active']
    list_filter = ['party_type', 'state_code', 'is_active']
    search_fields = ['party_name', 'party_code', 'gstin']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'item_code', 'unit', 'tax_rate', 'hsn_code', 'is_active']
    list_filter = ['unit', 'is_active']
    search_fields = ['item_name', 'item_code', 'hsn_code']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'gst_uqc', 'hsn_sac', 'is_active']
    search_fields = ['code', 'name', 'gst_uqc', 'hsn_sac']


@admin.register(Transporter)
class TransporterAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'gstin', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'gstin', 'phone']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'party', 'po_date', 'valid_until', 'status', 'company']
    list_filter = ['status']
    search_fields = ['po_number']
    raw_id_fields = ['party', 'company', 'created_by']
    inlines = [POItemInline]
