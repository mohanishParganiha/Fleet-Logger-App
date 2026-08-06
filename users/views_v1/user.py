from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from fleet.permissions import IsManager
from users.serializers_v1 import UserSerializer

User = get_user_model()


class UpdateUser(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):  # type:ignore
        User = get_user_model()
        return User.objects.all()

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [(IsAdminUser | IsManager)()]
        return [(IsManager | IsAdminUser)()]