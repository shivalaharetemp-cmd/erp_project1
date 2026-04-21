from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Company, User, CompanyUser


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompanySelectSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()

    def validate_company_id(self, value):
        request = self.context.get('request')
        if request and request.user:
            if not request.user.has_company_access(value):
                raise serializers.ValidationError("You don't have access to this company.")
        return value


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'role_display', 'is_active', 'default_company',
            'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    companies = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password', 'role', 'companies']

    def create(self, validated_data):
        companies_data = validated_data.pop('companies', [])
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        for company_id in companies_data:
            try:
                CompanyUser.objects.create(
                    user=user, company_id=company_id, role=user.role
                )
            except Exception:
                pass
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials.")
            if not user.is_active:
                raise serializers.ValidationError("User account is inactive.")
        else:
            raise serializers.ValidationError("Must include username and password.")

        attrs['user'] = user
        return attrs


class CompanyContextSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    company_name = serializers.CharField()
    company_code = serializers.CharField()
    user_role = serializers.CharField()
    financial_year = serializers.CharField()
