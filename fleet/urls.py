from django.urls import path
from . import views
from users.views import UpdateUser
urlpatterns = [
    # login endpoint
    path('login/', views.LoginView.as_view(), name='login'),

    # logout endpoint
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # user endpoints
    path('users/<uuid:pk>/', UpdateUser.as_view(), name='user-detail'),

    # truck endpoints
    path(
        'vehicles/', views.VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path(
        'vehicles/<uuid:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),

    # driver endpoints
    path(
        'drivers/', views.DriverListCreateView.as_view(), name='driver-list-create'),
    path(
        'drivers/<uuid:pk>/', views.DriverDetailView.as_view(), name='driver-detail'),

    # log endpoints
    path(
        'trip-logs/', views.TripLogListCreateView.as_view(), name='triplog-list-create'),
    path(
        'trip-logs/calculate-bulk/', views.TripLogBulkCalculateView.as_view(), name='triplog-calculate-bulk'),
    path(
        'trip-logs/<uuid:pk>/', views.TripLogDetailView.as_view(), name='triplog-detail'),
    path(
        'trip-logs/<uuid:pk>/approve/', views.TripLogApproveView.as_view(), name='triplog-approve'
    ),
    path(
        'trip-logs/<uuid:pk>/calculate/', views.TripLogCalculationView.as_view(), name='triplog-calculate'
    )
]
