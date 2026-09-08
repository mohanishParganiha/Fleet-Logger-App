from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound, PermissionDenied
from fleet.models import Driver
from django.db.models import ProtectedError
from fleet.serializers_v1 import DriverCreateSerializer, DriverSerializer, DriverSelfSerializer, DriverUpdateSerializer
from fleet.filters import DriverFilter
from fleet.permissions import IsManager


class DriverListCreateView(generics.ListCreateAPIView):
    """Viewset only for listing driver, creating driver along side creating user"""
    queryset = Driver.objects.all().select_related('user', 'primary_vehicle')
    filter_backends = [DjangoFilterBackend]
    filterset_class = DriverFilter

    def get_permissions(self):
        return [(IsAdminUser | IsManager)()]

    def get_serializer_class(self):  # type: ignore
        if self.request.method == 'POST':
            return DriverCreateSerializer
        return DriverSerializer


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    """viewset only for retrieve,update,delete driver with <pk>, by users with admin/manager permissions"""
    queryset = Driver.objects.all().select_related('user', 'primary_vehicle')
    permission_classes = [IsAdminUser | IsManager]

    def get_serializer_class(self):  # type: ignore
        if self.request.method in ['PUT', 'PATCH']:
            return DriverUpdateSerializer
        return DriverSerializer

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied(
            'You cannot delete driver, delete the user.', code=status.HTTP_403_FORBIDDEN)


class DriverMeView(generics.RetrieveUpdateDestroyAPIView):
    """viewset to retrieve, update self driver without <pk>, by authenticated user"""
    serializer_class = DriverSelfSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        return Driver.objects.filter(user=self.request.user).select_related('user', 'primary_vehicle')

    def get_object(self):  # type: ignore
        obj = self.get_queryset().first()
        if not obj:
            raise NotFound(
                'No driver found for this user', code=status.HTTP_404_NOT_FOUND
            )
        return obj

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied(
            'You cannot delete your self!, contact admin.', code=status.HTTP_403_FORBIDDEN)
