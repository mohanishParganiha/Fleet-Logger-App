from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError

from fleet.models import Vehicle, Driver
from fleet.serializers_v1 import VehicleSerializer
from fleet.filters import VehicleFilter
from fleet.permissions import IsManager, IsActiveDriver


class VehicleListCreateView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = VehicleFilter

    def get_permissions(self):
        if self.request.method == 'POST':
            return [(IsAdminUser | IsManager)()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_manager:  # type: ignore
            return Vehicle.objects.all()
        return Vehicle.objects.filter(
            id=self.request.user.driver_profile.primary_vehicle.id)  # type: ignore


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        return [(IsAdminUser | IsManager)()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            if instance.status in ('inactive', 'Inactive'):
                return Response(
                    {"detail": "This vehicle cannot be deleted because it is linked to active trip logs. It is already marked as inactive."},
                    status=status.HTTP_204_NO_CONTENT
                )
            instance.status = 'inactive'
            instance.save(update_fields=['status'])

            # set the linked driver primary_vehicle none.
            Driver.objects.filter(
                primary_vehicle=instance.id).update(primary_vehicle=None)

            return Response(
                {"detail": "This vehicle cannot be deleted because it is linked to active trip logs. Its status has now been set to inactive."},
                status=status.HTTP_204_NO_CONTENT
            )
