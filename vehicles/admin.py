from django.contrib import admin
from .models import Vehicle, VehicleItem, VehicleChangeLog


class VehicleItemInline(admin.TabularInline):
    model = VehicleItem
    extra = 0
    raw_id_fields = ['item']


class VehicleChangeLogInline(admin.TabularInline):
    model = VehicleChangeLog
    extra = 0
    readonly_fields = ['old_vehicle_number', 'new_vehicle_number', 'changed_by', 'reason', 'changed_at']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_number', 'transporter', 'party', 'status', 'created_by', 'loaded_at', 'cancelled_at', 'company']
    list_filter = ['status']
    search_fields = ['vehicle_number', 'party__party_name', 'transporter__name']
    raw_id_fields = ['transporter', 'party', 'created_by', 'cancelled_by', 'company']
    inlines = [VehicleItemInline, VehicleChangeLogInline]


@admin.register(VehicleItem)
class VehicleItemInlineAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'item', 'quantity', 'unloaded_quantity']
    raw_id_fields = ['vehicle', 'item']


@admin.register(VehicleChangeLog)
class VehicleChangeLogAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'old_vehicle_number', 'new_vehicle_number', 'changed_by', 'changed_at']
    raw_id_fields = ['vehicle', 'changed_by']
