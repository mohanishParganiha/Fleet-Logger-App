from django.urls import path
from fleet.views_v1 import (
    CustomTokenObtainPairView, CustomLogoutView, CustomTokenRefreshView,
    VehicleListCreateView, VehicleDetailView,
    DriverListCreateView, DriverDetailView, DriverMeView,
    TripLogListCreateView, TripLogDetailView,
    TripLogApproveView, TripLogCalculationView, TripLogBulkCalculateView,
)
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    # login endpoint
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),

    # token refresh view
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),

    # logout endpoint
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # token verify
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # truck endpoints
    path(
        'vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path(
        'vehicles/<uuid:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),

    # driver endpoints
    path(
        'drivers/', DriverListCreateView.as_view(), name='driver-list-create'),
    path(
        'drivers/<uuid:pk>/', DriverDetailView.as_view(), name='driver-detail'),
    path(
        'drivers/me', DriverMeView.as_view(), name='driver-me-detail'),

    # log endpoints
    path(
        'trip-logs/', TripLogListCreateView.as_view(), name='triplog-list-create'),
    path(
        'trip-logs/calculate-bulk/', TripLogBulkCalculateView.as_view(), name='triplog-calculate-bulk'),
    path(
        'trip-logs/<uuid:pk>/', TripLogDetailView.as_view(), name='triplog-detail'),
    path(
        'trip-logs/<uuid:pk>/approve/', TripLogApproveView.as_view(), name='triplog-approve'
    ),
    path(
        'trip-logs/<uuid:pk>/calculate/', TripLogCalculationView.as_view(), name='triplog-calculate'
    )
]
