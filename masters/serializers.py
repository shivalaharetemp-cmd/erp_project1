from rest_framework import serializers
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_gstin(self, value):
        if value and len(value) != 15:
            raise serializers.ValidationError("GSTIN must be exactly 15 characters.")
        return value


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_hsn_code(self, value):
        if value and len(value) != 8:
            raise serializers.ValidationError("HSN code must be exactly 8 digits.")
        return value


class TransporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transporter
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_gstin(self, value):
        if value and len(value) != 15:
            raise serializers.ValidationError("GSTIN must be exactly 15 characters.")
        return value


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.item_name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
        read_only_fields = ['id', 'fulfilled_quantity']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)
    party_name = serializers.CharField(source='party.party_name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        po = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=po, **item_data)
        return po

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        instance = super().update(instance, validated_data)
        return instance
