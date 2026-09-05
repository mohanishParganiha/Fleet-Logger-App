from django.urls import path
from fleet.views_v1 import (
    LoginView, LogoutView,
    VehicleListCreateView, VehicleDetailView,
    DriverListCreateView, DriverDetailView, DriverMeView,
    TripLogListCreateView, TripLogDetailView,
    TripLogApproveView, TripLogCalculationView, TripLogBulkCalculateView,
)

urlpatterns = [
    # login endpoint
    path('login/', LoginView.as_view(), name='login'),

    # logout endpoint
    path('logout/', LogoutView.as_view(), name='logout'),

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
