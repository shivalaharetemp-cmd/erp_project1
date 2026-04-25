from rest_framework import serializers
from .models import Vehicle, VehicleItem, VehicleChangeLog


class VehicleItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.item_name', read_only=True)
    item_code = serializers.CharField(source='item.item_code', read_only=True)
    unit = serializers.CharField(source='item.unit', read_only=True)

    class Meta:
        model = VehicleItem
        fields = '__all__'
        read_only_fields = ['id', 'unloaded_quantity']


class VehicleListSerializer(serializers.ModelSerializer):
    transporter_name = serializers.CharField(source='transporter.name', read_only=True)
    party_name = serializers.CharField(source='party.party_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    has_freight = serializers.SerializerMethodField()
    has_invoice = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_number', 'transporter_name', 'party_name',
            'status', 'driver_name', 'driver_phone', 'items_count',
            'has_freight', 'has_invoice', 'created_by_name',
            'loaded_at', 'cancelled_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_has_freight(self, obj):
        return obj.freights.filter(is_active=True).exists()

    def get_has_invoice(self, obj):
        return hasattr(obj, 'sale') and obj.sale is not None


class VehicleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'transporter', 'party', 'driver_name', 'driver_phone']

    def validate_vehicle_number(self, value):
        request = self.context.get('request')
        company_id = getattr(request, 'company_id', None)
        if company_id:
            # Check for pending vehicles with same number
            existing = Vehicle.objects.filter(
                company_id=company_id, vehicle_number=value,
                status='Pending'
            ).exists()
            if existing:
                raise serializers.ValidationError(
                    "A pending vehicle with this number already exists."
                )
        return value


class VehicleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['transporter', 'party', 'driver_name', 'driver_phone']


class VehicleLoadSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="List of items: [{'item_id': uuid, 'quantity': decimal}]"
    )

    def validate_items(self, value):
        validated = []
        for item_data in value:
            item_id = item_data.get('item_id')
            quantity = item_data.get('quantity')
            if not item_id:
                raise serializers.ValidationError("Each item must have an item_id.")
            if not quantity or float(quantity) <= 0:
                raise serializers.ValidationError("Quantity must be greater than 0.")
            validated.append({
                'item_id': item_id,
                'quantity': quantity
            })
        return validated


class VehicleCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5, help_text="Cancellation reason (min 5 characters)")


class VehicleChangeSerializer(serializers.Serializer):
    new_vehicle_number = serializers.CharField(max_length=20)
    reason = serializers.CharField(min_length=5)


class VehicleChangeLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = VehicleChangeLog
        fields = '__all__'
        read_only_fields = ['id', 'changed_at']
