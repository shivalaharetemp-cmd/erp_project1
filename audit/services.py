import json
from .models import AuditLog


class AuditService:
    """Service for logging audit trails."""

    @staticmethod
    def log(user, company, action, model_name='', object_id='',
            old_value=None, new_value=None, reason='', request=None):
        """Create an audit log entry."""
        ip_address = None
        user_agent = ''

        if request:
            ip_address = AuditService._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Serialize values
        old_value = AuditService._serialize(old_value) if old_value else {}
        new_value = AuditService._serialize(new_value) if new_value else {}

        AuditLog.objects.create(
            user=user,
            company=company,
            action=action,
            model_name=model_name,
            object_id=object_id,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def _serialize(value):
        """Convert value to JSON-serializable dict."""
        if hasattr(value, '__dict__'):
            try:
                from django.forms.models import model_to_dict
                return model_to_dict(value)
            except Exception:
                return str(value)
        return value if isinstance(value, dict) else {'value': str(value)}
