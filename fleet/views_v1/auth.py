from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from config import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from fleet.serializers_v1 import LoginRequestSerializer, LoginResponseSerializer
from services_v1.auth_service.auth_service import AuthService


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')  # type: ignore
            refresh_token = response.data.get('refresh')  # type: ignore

            # Clean response body data for security
            response.data = {"message": "Login successful"}

            # Attach HttpOnly cookies
            response = AuthService.set_jwt_cookies(
                response, access_token, refresh_token)
        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Extract refresh token from cookie if not in request body
        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token and 'refresh' not in request.data:  # type: ignore
            request.data['refresh'] = refresh_token  # type: ignore

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')  # type: ignore
            # Only if ROTATE_REFRESH_TOKENS=True
            refresh_token = response.data.get('refresh')  # type: ignore

            response.data = {"message": "Token refresh successful"}
            response = AuthService.set_jwt_cookies(
                response, access_token, refresh_token)
        return response


@extend_schema(
    methods=['POST'],
    request=None,
    responses={
        200: OpenApiResponse(
            response=None,
            description="Successfully logged out.",
            examples=[{"message": "Logout successful"}]
        )
    },
    parameters=[
        OpenApiParameter(
            name='Set-Cookie',
            type=str,
            location=OpenApiParameter.HEADER,
            description="Clears the authentication token cookie by forcing max-age=0",
            response=True
        )
    ],
    description="Logout view for httponly cookie wipe from client browser."
)
class CustomLogoutView(APIView):
    """Logout view for httponly cookie wipe from client browser"""

    def post(self, request):
        response = Response({"message": "Logout successful"})
        response.delete_cookie(
            settings.SIMPLE_JWT['AUTH_COOKIE'], path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'])
        response.delete_cookie(
            settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'])
        return response
