from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = fields
