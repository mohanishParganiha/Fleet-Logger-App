"""Business logic for authentication."""
from django.conf import settings


class AuthService:
    """Business logic for authentication."""

    @staticmethod
    def set_jwt_cookies(response, access_token, refresh_token=None):
        cookie_settings = settings.SIMPLE_JWT

        # set access token cookie
        response.set_cookie(
            key=cookie_settings['AUTH_COOKIE'],
            value=access_token,
            expires=cookie_settings['ACCESS_TOKEN_LIFETIME'],
            secure=cookie_settings['AUTH_COOKIE_SECURE'],
            httponly=cookie_settings['AUTH_COOKIE_HTTP_ONLY'],
            samesite=cookie_settings['AUTH_COOKIE_SAMESITE'],
            path=cookie_settings['AUTH_COOKIE_PATH'],
            # domain=cookie_settings['AUTH_COOKIE_DOMAIN'],
        )

        # set refresh token cookie if provided
        if refresh_token:
            response.set_cookie(
                key=cookie_settings['AUTH_COOKIE_REFRESH'],
                value=refresh_token,
                expires=cookie_settings['REFRESH_TOKEN_LIFETIME'],
                secure=cookie_settings['AUTH_COOKIE_SECURE'],
                httponly=cookie_settings['AUTH_COOKIE_HTTP_ONLY'],
                samesite=cookie_settings['AUTH_COOKIE_SAMESITE'],
                path=cookie_settings['AUTH_COOKIE_PATH'],
                # domain=cookie_settings['AUTH_COOKIE_DOMAIN'],
            )
        return response
