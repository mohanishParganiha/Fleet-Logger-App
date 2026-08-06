from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from fleet.serializers_v1 import LoginRequestSerializer, LoginResponseSerializer
from services_v1.auth_service.auth_service import AuthService


@extend_schema(
    request=LoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=LoginResponseSerializer,
            description="Successfully authenticated. Returns profile metadata."
        )
    },
    parameters=[
        OpenApiParameter(
            name='Set-Cookie',
            type=str,
            location=OpenApiParameter.HEADER,
            description="Contains auth_token=...; HttpOnly; Secure; SameSite; domain;",
            response=True
        )
    ],
    description="Authenticates credentials, returns profile metadata, and drops a secure HttpOnly cookie."
)
class LoginView(APIView):
    """login endpoint - returns auth token"""
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user, token = AuthService.login_user(email, password)
        except ValueError as e:
            error_msg = str(e)
            if "empty" in error_msg:
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": error_msg}, status=status.HTTP_401_UNAUTHORIZED)

        return AuthService.create_login_response_with_cookie(user, token)


@extend_schema(
    request=None,
    responses={
        200: OpenApiResponse(
            response=None,
            description="Successfully logged out."
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
    description="Permanently deletes the database token and instructs the browser to erase the HttpOnly cookie."
)
class LogoutView(APIView):
    """View to clear cookies on logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        AuthService.logout_user(request.auth)
        return AuthService.create_logout_response()