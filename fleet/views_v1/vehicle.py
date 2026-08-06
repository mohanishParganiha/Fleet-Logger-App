from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from fleet.models import Vehicle
from fleet.serializers_v1 import VehicleSerializer
from fleet.filters import VehicleFilter
from fleet.permissions import IsManager


class VehicleListCreateView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = VehicleFilter

    def get_permissions(self):
        if self.request.method == "POST":
            return [(IsAdminUser | IsManager)()]
        return [IsAuthenticated()]


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        elif self.request.method == "GET":
            return [IsAuthenticated()]
        return [(IsAdminUser | IsManager)()]