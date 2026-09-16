from django.db import connection, OperationalError, InterfaceError
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
# class HealthCheckView(APIView):
#     """Health check endpoint for container orchestration."""
#     permission_classes = [AllowAny]
#     def get(self, request):
#         try:
#             # Forces Django to test the actual connection to the remote DB
#             connection.ensure_connection()
#             return Response("Healthy", status=status.HTTP_200_OK)
#         except Exception:
#             # Returns a 500 Internal Server Error if the DB is unreachable
#             return Response("Database Unreachable", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class HealthCheckView(APIView):
    """
    Health check endpoint for container orchestration (Docker/Kubernetes).
    Verifies that the API server is up and the database is healthy.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "services": {
                "api": "up",
                "database": "connected"
            }
        }

        try:
            # Forces Django to test the actual connection to the remote DB
            connection.ensure_connection()
            return Response(health_status, status=status.HTTP_200_OK)

        except (OperationalError, InterfaceError) as e:
            # The database server itself is down, unreachable, or timed out
            health_status["status"] = "unhealthy"
            health_status["services"]["database"] = "unreachable"
            return Response(health_status, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Catch-all for misconfigurations (like wrong DB name or credentials)
            health_status["status"] = "unhealthy"
            health_status["services"]["database"] = "configuration_error"
            return Response(health_status, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
