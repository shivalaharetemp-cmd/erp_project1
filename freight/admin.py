from django.contrib import admin
from .models import Freight, ReturnFreight


@admin.register(Freight)
class FreightAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'freight_type', 'quantity', 'rate', 'amount', 'is_active', 'created_by', 'company']
    list_filter = ['freight_type', 'is_active']
    search_fields = ['vehicle__vehicle_number']
    raw_id_fields = ['vehicle', 'created_by', 'company']


@admin.register(ReturnFreight)
class ReturnFreightAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'credit_note', 'freight_type', 'amount', 'created_by', 'company']
    list_filter = ['freight_type']
    raw_id_fields = ['vehicle', 'credit_note', 'created_by', 'company']
