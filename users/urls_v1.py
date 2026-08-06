from django.urls import path
from users.views_v1 import UpdateUser

urlpatterns = [
    path('users/<uuid:pk>/', UpdateUser.as_view(), name='user-detail'),
]