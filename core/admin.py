from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, User, CompanyUser


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'state', 'state_code', 'gstin', 'is_active', 'created_at']
    list_filter = ['is_active', 'state_code']
    search_fields = ['name', 'code', 'gstin']


class CompanyUserInline(admin.TabularInline):
    model = CompanyUser
    extra = 0
    raw_id_fields = ['company']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ERP Info', {'fields': ('phone', 'role', 'default_company')}),
    )
    inlines = [CompanyUserInline]


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    raw_id_fields = ['user', 'company']
