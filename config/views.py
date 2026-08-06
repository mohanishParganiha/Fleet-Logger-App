from django.db import connection
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


class HealthCheckView(APIView):
    """Health check endpoint for container orchestration."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

        return Response({
            "status": "healthy",
            "database": db_status
        }, status=status.HTTP_200_OK)