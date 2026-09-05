from django.urls import path
from users.views_v1 import UserDetailView, ChangePasswordView, UserListView

urlpatterns = [
    path('users/', UserListView.as_view(), name='users-list'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path(
        'users/me/change-password/', ChangePasswordView.as_view(), name='user-me-chagne-password'),
]
