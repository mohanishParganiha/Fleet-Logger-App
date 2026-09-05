from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from users.serializers_v1 import UserSerializer, SetPasswordSerializer
from fleet.permissions import IsManager

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


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):  # type: ignore
        return self.request.user
