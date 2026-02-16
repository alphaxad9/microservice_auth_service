# src/infrastructure/apps/users/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from typing import Optional, Any

class JWTCookieAuthentication(BaseAuthentication):
    def authenticate(self, request: Any) -> Optional[tuple]:
        # Check for token in cookies
        try:
            access_token = request.COOKIES.get(settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access'))
        except AttributeError:
            raise AuthenticationFailed('SIMPLE_JWT settings are misconfigured: AUTH_COOKIE missing')

        if not access_token:
            # Fall back to header-based authentication
            header = request.META.get(settings.SIMPLE_JWT.get('AUTH_HEADER_NAME', 'HTTP_AUTHORIZATION'))
            auth_types = settings.SIMPLE_JWT.get('AUTH_HEADER_TYPES', ('Bearer',))
            if header and any(header.startswith(auth_type) for auth_type in auth_types):
                access_token = header.split(' ')[1]
            else:
                return None

        # Validate JWT token
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(access_token)
            user = jwt_auth.get_user(validated_token)
            return (user, validated_token)
        except Exception as e:
            raise AuthenticationFailed(f'Invalid or expired token: {str(e)}')

    def authenticate_credentials(self, username: str, password: str) -> Optional[Any]:
        """
        Used by TokenObtainPairView to authenticate with username or email.
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(Q(username=username) | Q(email=username))
        except UserModel.DoesNotExist:
            # Run a dummy password hash to prevent timing attacks
            UserModel().set_password(password)
            return None

        if user.check_password(password) and user.is_active:
            return user
        return None