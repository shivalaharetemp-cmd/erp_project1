from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied


class CompanyContextMiddleware(MiddlewareMixin):
    """
    Ensures that every authenticated request has a company context.
    Validates company_id from session on every request.
    """
    COMPANY_EXEMPT_PATHS = [
        '/api/auth/',
        '/admin/',
        '/api/audit/',
    ]

    def process_request(self, request):
        if not request.user or not request.user.is_authenticated:
            return None

        path = request.path
        # Allow access to exempt paths without company context
        for exempt_path in self.COMPANY_EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return None

        # For all other API paths, require company context
        if path.startswith('/api/'):
            company_id = request.session.get('company_id')
            if not company_id:
                raise PermissionDenied("Company not selected. Please select a company first.")

            # Set company_id on request for easy access in views
            request.company_id = company_id

        return None
