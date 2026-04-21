from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Company(models.Model):
    """Multi-company support - complete data isolation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    state = models.CharField(max_length=100)
    state_code = models.CharField(max_length=2)
    gstin = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def financial_year(self):
        """Returns current financial year string e.g. '2024-25'."""
        from django.utils import timezone
        today = timezone.now().date()
        if today.month >= 4:
            return f"{today.year}-{str(today.year + 1)[-2:]}"
        else:
            return f"{today.year - 1}-{str(today.year)[-2:]}"


class User(AbstractUser):
    """Custom user model with company association."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    default_company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='default_users'
    )

    # Role choices
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_OPERATOR = 'operator'
    ROLE_VIEWER = 'viewer'
    ROLE_AUDITOR = 'auditor'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_OPERATOR, 'Operator'),
        (ROLE_VIEWER, 'Viewer'),
        (ROLE_AUDITOR, 'Auditor'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_OPERATOR)

    class Meta:
        verbose_name = 'User'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def has_company_access(self, company_id):
        return self.company_users.filter(company_id=company_id, is_active=True).exists()

    def has_role_permission(self, required_roles):
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        return self.role in required_roles


class CompanyUser(models.Model):
    """Many-to-many relationship between User and Company with role override."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_users')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_users')
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_OPERATOR)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'company')
        verbose_name = 'Company User'

    def __str__(self):
        return f"{self.user.username} - {self.company.code} ({self.get_role_display()})"
