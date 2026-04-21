from django.db import models
import uuid


class AuditLog(models.Model):
    """Complete audit trail for all operations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    company = models.ForeignKey('core.Company', on_delete=models.SET_NULL, null=True, related_name='audit_logs')

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('CANCEL', 'Cancel'),
        ('LOAD', 'Load'),
        ('CHANGE_VEHICLE', 'Change Vehicle'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('SELECT_COMPANY', 'Select Company'),
        ('GENERATE_INVOICE', 'Generate Invoice'),
        ('GENERATE_CREDIT_NOTE', 'Generate Credit Note'),
        ('REVERSE', 'Reverse'),
        ('PERMISSION_DENIED', 'Permission Denied'),
    ]
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.action} on {self.model_name}"
