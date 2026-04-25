from rest_framework import serializers
from .models import Freight, ReturnFreight


class FreightSerializer(serializers.ModelSerializer):
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)

    class Meta:
        model = Freight
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        freight_type = attrs.get('freight_type')
        quantity = attrs.get('quantity')
        rate = attrs.get('rate')
        amount = attrs.get('amount')

        if freight_type in ('PerQuantity', 'Guaranteed'):
            if not quantity or quantity <= 0:
                raise serializers.ValidationError({"quantity": "Quantity is required and must be > 0."})
            if not rate or rate <= 0:
                raise serializers.ValidationError({"rate": "Rate is required and must be > 0."})
            attrs['amount'] = quantity * rate
        elif freight_type == 'Fixed':
            if not amount or amount <= 0:
                raise serializers.ValidationError({"amount": "Amount is required and must be > 0."})

        return attrs


class ReturnFreightSerializer(serializers.ModelSerializer):
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    credit_note_number = serializers.CharField(source='credit_note.credit_note_number', read_only=True)

    class Meta:
        model = ReturnFreight
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_by', 'created_at']

    def validate(self, attrs):
        freight_type = attrs.get('freight_type')
        quantity = attrs.get('quantity')
        rate = attrs.get('rate')
        amount = attrs.get('amount')

        if freight_type in ('PerQuantity', 'Guaranteed'):
            if not quantity or quantity <= 0:
                raise serializers.ValidationError({"quantity": "Quantity is required and must be > 0."})
            if not rate or rate <= 0:
                raise serializers.ValidationError({"rate": "Rate is required and must be > 0."})
            attrs['amount'] = quantity * rate
        elif freight_type == 'Fixed':
            if not amount or amount <= 0:
                raise serializers.ValidationError({"amount": "Amount is required and must be > 0."})

        return attrs
