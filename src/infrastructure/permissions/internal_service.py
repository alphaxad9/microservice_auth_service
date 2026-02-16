from rest_framework.permissions import BasePermission
from django.conf import settings

class IsInternalService(BasePermission):
    """
    Allows access only to trusted internal services that provide the correct
    X-Internal-Key header.
    """
    def has_permission(self, request, view):
        provided_key = request.headers.get("X-Internal-Key")
        expected_key = settings.INTERNAL_API_KEY
        
        if provided_key == expected_key:
            return True
            
        # Log failed attempts (useful in production)
        if provided_key is not None:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Invalid internal API key attempt from {request.META.get('REMOTE_ADDR')}"
            )
        return False