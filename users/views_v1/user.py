from django.contrib.auth import get_user_model
from rest_framework import generics, response, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from users.serializers_v1 import UserSerializer, SetPasswordSerializer
from fleet.permissions import IsManager
from django.db.models import ProtectedError
from fleet.models import Driver

User = get_user_model()


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAdminUser | IsManager]


class UserDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):  # type:ignore
        if self.request.user.is_staff or self.request.user.is_manager:  # type: ignore
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)  # type: ignore

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            if not instance.is_active:
                return response.Response(
                    {"detail": "This user account and driver profile are already marked as inactive."},
                    status=status.HTTP_204_NO_CONTENT
                )
            # update the use(instance)
            instance.is_active = False
            # change email and password later so it no one can login the user.
            instance.save(update_fields=['is_active'])

            # if it fails , then driver exist, list the objects of driver

            if instance.driver_profile.triplog_set.exists():
                # if driver has triplogs then set driver status to inactive, driver vehicle to null.
                instance.driver_profile.status = 'inactive'
                instance.driver_profile.primary_vehicle = None
                instance.driver_profile.save(
                    update_fields=['status', 'primary_vehicle'])

        return response.Response(
            {"detail": "The linked driver profile has historical trip logs and cannot be hard-deleted. As a fallback, both the user account and driver profile have been disabled."},
            status=status.HTTP_204_NO_CONTENT
        )


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):  # type: ignore
        return self.request.user
