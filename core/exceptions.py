from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import uuid
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    request_id = str(uuid.uuid4())[:8]

    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': {
                'code': getattr(exc, 'error_code', 'UNKNOWN_ERROR'),
                'message': str(exc),
                'details': getattr(exc, 'error_details', {}),
                'request_id': request_id,
            }
        }
        response.data = error_data
    else:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'An unexpected error occurred.',
                    'details': {},
                    'request_id': request_id,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


class ERPValidationError(Exception):
    def __init__(self, message, code='VALIDATION_ERROR', details=None):
        self.message = message
        self.error_code = code
        self.error_details = details or {}
        super().__init__(self.message)


class ERPPermissionError(Exception):
    def __init__(self, message, code='PERM_001', details=None):
        self.message = message
        self.error_code = code
        self.error_details = details or {}
        super().__init__(self.message)


class ERPBusinessError(Exception):
    def __init__(self, message, code='BUSINESS_ERROR', details=None):
        self.message = message
        self.error_code = code
        self.error_details = details or {}
        super().__init__(self.message)
