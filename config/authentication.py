from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from config import settings
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import Token


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        header = self.get_header(request)

        if header is None:
            raw_token = request.COOKIES.get(
                settings.SIMPLE_JWT['AUTH_COOKIE']) or None
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


class CustomJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    # Path to your class
    target_class = 'config.authentication.CustomJWTAuthentication'
    name = 'JWT_Auth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            # The actual cookie key name
            'name': 'access_token',
        }
