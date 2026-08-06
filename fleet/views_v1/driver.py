from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from fleet.models import Driver
from fleet.serializers_v1 import DriverSerializer
from fleet.filters import DriverFilter
from fleet.permissions import IsManager


class DriverListCreateView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DriverFilter

    def get_permissions(self):
        if self.request.method == "POST":
            return [(IsAdminUser | IsManager)()]
        return [IsAuthenticated()]


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        elif self.request.method == "GET":
            return [IsAuthenticated()]
        return [(IsAdminUser | IsManager)()]