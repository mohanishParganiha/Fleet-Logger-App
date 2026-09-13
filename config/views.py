from django.db import connection
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    methods=['GET'],
    responses={
        200: OpenApiResponse(
            response=None,
            description="Service is healthy",
            examples=[
                {
                    "status": "healthy",
                    "database": "connected"
                }
            ]
        )
    },
    description="Health check endpoint for container orchestration.",
)
class HealthCheckView(APIView):
    """Health check endpoint for container orchestration."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Forces Django to test the actual connection to the remote DB
            connection.ensure_connection()
            return Response("Healthy", status=200)
        except Exception:
            # Returns a 500 Internal Server Error if the DB is unreachable
            return Response("Database Unreachable", status=500)
