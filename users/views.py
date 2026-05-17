from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from fleet.permissions import IsManager
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class CreateUser(generics.CreateAPIView):
    permission_classes = [IsManager | IsAdminUser]
    serializer_class = RegisterSerializer

    def get_queryset(self):  # type:ignore
        User = get_user_model()
        return User.objects.all()


class UpdateUser(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):  # type:ignore
        User = get_user_model()
        return User.objects.all()

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdminUser]
        return [(IsManager | IsAdminUser)()]
