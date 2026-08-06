"""Business logic for authentication."""
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.conf import settings


class AuthService:
    """Business logic for authentication."""

    @staticmethod
    def login_user(email: str, password: str):
        """Authenticate user and return (user, token). Raises on failure."""
        if not email or not password:
            raise ValueError("username or password cannot be empty")

        user = authenticate(email=email, password=password)
        if not user:
            raise ValueError("Invalid credentials")

        token, _ = Token.objects.get_or_create(user=user)
        return user, token

    @staticmethod
    def create_login_response(user, token):
        """Build response data with user metadata."""
        return {
            "user_id": user.id,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_manager": user.is_manager,
        }

    @staticmethod
    def get_cookie_settings():
        """Return cookie settings dict from Django settings."""
        return {
            'httponly': settings.SESSION_COOKIE_HTTPONLY,
            'secure': settings.SESSION_COOKIE_SECURE,
            'samesite': settings.SESSION_COOKIE_SAMESITE,
            'domain': settings.SESSION_COOKIE_DOMAIN,
        }

    @staticmethod
    def create_login_response_with_cookie(user, token):
        """Create Response with user data and auth cookie already set."""
        response_data = AuthService.create_login_response(user, token)
        response = Response(response_data)
        response.set_cookie(key='auth_token', value=token.key, **AuthService.get_cookie_settings())
        return response

    @staticmethod
    def logout_user(auth_token):
        """Delete token from database."""
        if auth_token:
            auth_token.delete()

    @staticmethod
    def get_logout_cookie_settings():
        """Return cookie settings for logout (expired)."""
        base = AuthService.get_cookie_settings()
        return {
            **base,
            'max_age': 0,
            'expires': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'value': '',
        }

    @staticmethod
    def create_logout_response():
        """Create Response with logout cookie already set."""
        response = Response({"detail": "Successfully logged out."}, status=200)
        response.set_cookie(key='auth_token', **AuthService.get_logout_cookie_settings())
        return response