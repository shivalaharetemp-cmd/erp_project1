from django.contrib import admin
from .models import Stock, StockMovement, StockAdjustment


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item', 'company', 'quantity', 'reserved_quantity', 'available_quantity']
    list_filter = ['company']
    search_fields = ['item__item_name', 'item__item_code']
    raw_id_fields = ['company', 'item']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_type', 'item', 'company', 'quantity', 'created_at']
    list_filter = ['movement_type', 'company', 'created_at']
    search_fields = ['item__item_name', 'reference_no']
    raw_id_fields = ['company', 'item', 'purchase_order', 'sale', 'vehicle']


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['adjustment_type', 'item', 'company', 'difference', 'created_at', 'approved_by']
    list_filter = ['adjustment_type', 'company', 'created_at']
    search_fields = ['item__item_name', 'reason']
    raw_id_fields = ['company', 'item', 'created_by', 'approved_by']
