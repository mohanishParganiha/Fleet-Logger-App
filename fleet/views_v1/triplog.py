from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from fleet.models import TripLog
from fleet.serializers_v1 import (
    TripLogSerializer,
    TripCalculationInputSerializer,
    BulkCalculationInputSerializer
)
from fleet.filters import TripLogFilter
from fleet.permissions import IsManager

from services_v1.triplog_service.triplog_service import TripLogService
from services_v1.triplog_service.exceptions import TripNotFound, TripAlreadyApproved, InvalidCalculationInput


class TripLogListCreateView(generics.ListCreateAPIView):
    serializer_class = TripLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TripLogFilter

    def get_queryset(self):
        return TripLog.objects.with_relations()


class TripLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TripLogSerializer

    def get_queryset(self):
        return TripLog.objects.with_relations()

    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class TripLogApproveView(APIView):
    def get_permissions(self):
        return [(IsAdminUser | IsManager)()]

    def post(self, request, pk, *args, **kwargs):
        try:
            TripLogService.approve_trip(pk)
        except TripNotFound:
            return Response({"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)
        except TripAlreadyApproved as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "Success",
                "detail": f"Trip log id {pk} has been approved and locked."},
            status=status.HTTP_200_OK
        )


class TripLogCalculationView(APIView):
    """calculation rate for single trip"""
    permission_classes = [IsAdminUser | IsManager]

    def post(self, request, pk):
        serializer = TripCalculationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = TripLogService.calculate_single(
                pk, **serializer.validated_data)
        except TripNotFound:
            return Response({"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)
        except InvalidCalculationInput as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class TripLogBulkCalculateView(APIView):
    """calculate total rate for multiple trips in date range."""
    permission_classes = [IsAdminUser | IsManager]

    def post(self, request):
        serializer = BulkCalculationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = TripLogService.calculate_bulk(**serializer.validated_data)
        except InvalidCalculationInput as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except TripNotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)