from django.contrib import admin
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem, LoadingPoint, Unit, State, Country, Address


class POItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    raw_id_fields = ['item']


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['address_line_1', 'city', 'state', 'pincode', 'country']
    list_filter = ['state', 'country']
    search_fields = ['address_line_1', 'city', 'pincode']


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['party_name', 'party_code', 'party_type', 'address_state', 'gstin', 'is_active']
    list_filter = ['party_type', 'address__state', 'is_active']
    search_fields = ['party_name', 'party_code', 'gstin', 'address__city']
    raw_id_fields = ['address']

    def address_state(self, obj):
        return obj.address.state.name if obj.address else '-'
    address_state.short_description = 'State'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'item_code', 'unit', 'tax_rate', 'hsn_code', 'is_active']
    list_filter = ['unit', 'is_active']
    search_fields = ['item_name', 'item_code', 'hsn_code']


@admin.register(Transporter)
class TransporterAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'gstin', 'city', 'is_active']
    list_filter = ['is_active', 'address__state']
    search_fields = ['name', 'gstin', 'phone', 'address__city']
    raw_id_fields = ['address']

    def city(self, obj):
        return obj.address.city if obj.address else '-'
    city.short_description = 'City'


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'party', 'po_date', 'valid_until', 'status', 'company']
    list_filter = ['status']
    search_fields = ['po_number']
    raw_id_fields = ['party', 'company', 'created_by']
    inlines = [POItemInline]


@admin.register(LoadingPoint)
class LoadingPointAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
