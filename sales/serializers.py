from rest_framework import serializers
from .models import Sale, SaleItem, CreditNote, CreditNoteItem


class SaleItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.item_name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    hsn_code = serializers.CharField(read_only=True)
    unit = serializers.CharField(source='item.unit', read_only=True)

    class Meta:
        model = SaleItem
        fields = '__all__'
        read_only_fields = ['id']


class SaleListSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.party_name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'invoice_date', 'party_name',
            'vehicle_number', 'subtotal', 'total_tax', 'grand_total',
            'status', 'financial_year', 'created_at'
        ]
        read_only_fields = fields


class SaleDetailSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    party_name = serializers.CharField(source='party.party_name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = fields


class CreateSaleSerializer(serializers.Serializer):
    """Serializer for creating sale with rate per item."""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="[{'vehicle_item_id': uuid, 'rate': decimal}]"
    )

    def validate_items(self, value):
        validated = []
        for item in value:
            vehicle_item_id = item.get('vehicle_item_id')
            rate = item.get('rate')
            if not vehicle_item_id:
                raise serializers.ValidationError("vehicle_item_id is required.")
            if not rate or float(rate) <= 0:
                raise serializers.ValidationError("Rate must be > 0.")
            validated.append({'vehicle_item_id': vehicle_item_id, 'rate': rate})
        return validated


class CreditNoteItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.item_name', read_only=True)
    sale_item_quantity = serializers.DecimalField(
        source='sale_item.quantity', max_digits=15, decimal_places=3, read_only=True
    )

    class Meta:
        model = CreditNoteItem
        fields = '__all__'
        read_only_fields = ['id']


class CreditNoteCreateSerializer(serializers.Serializer):
    sale_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="[{'sale_item_id': uuid, 'quantity': decimal, 'rate': decimal(optional)}]"
    )

    def validate_items(self, value):
        validated = []
        for item in value:
            sale_item_id = item.get('sale_item_id')
            quantity = item.get('quantity')
            rate = item.get('rate', None)
            if not sale_item_id:
                raise serializers.ValidationError("sale_item_id is required.")
            if not quantity or float(quantity) <= 0:
                raise serializers.ValidationError("Quantity must be > 0.")
            validated.append({
                'sale_item_id': sale_item_id,
                'quantity': quantity,
                'rate': rate
            })
        return validated


class CreditNoteListSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.party_name', read_only=True)
    original_invoice = serializers.CharField(source='sale.invoice_number', read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            'id', 'credit_note_number', 'credit_note_date', 'party_name',
            'original_invoice', 'subtotal', 'total_tax', 'grand_total',
            'status', 'financial_year', 'created_at'
        ]
        read_only_fields = fields


class CreditNoteDetailSerializer(serializers.ModelSerializer):
    items = CreditNoteItemSerializer(many=True, read_only=True)
    party_name = serializers.CharField(source='party.party_name', read_only=True)
    original_invoice = serializers.CharField(source='sale.invoice_number', read_only=True)

    class Meta:
        model = CreditNote
        fields = '__all__'
        read_only_fields = fields
