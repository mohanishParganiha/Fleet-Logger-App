from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # 1. Look for the token inside the HttpOnly cookie payload
        token_string = request.COOKIES.get('auth_token')

        # 2. If cookie is missing, return None to let other auth methods try
        if not token_string:
            return None

        # 3. Use DRF's built-in validation logic to check the database token string
        return self.authenticate_credentials(token_string)


class CookieTokenAuthExtension(OpenApiAuthenticationExtension):
    # Path to your class
    target_class = 'your_app_name.authentication.CookieTokenAuthentication'
    name = 'CookieAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'auth_token',  # The actual cookie key name
        }
