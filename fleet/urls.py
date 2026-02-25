from django.urls import path
from . import views

urlpatterns = [
    # login endpoint
    path('login/', views.LoginView.as_view(), name='login'),

    # truck endpoints
    path(
        'vehicles/', views.VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path(
        'vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),

    # driver endpoints
    path(
        'drivers/', views.DriverListCreateView.as_view(), name='driver-list-create'),
    path(
        'drivers/<int:pk>/', views.DriverDetailView.as_view(), name='driver-detail'),

    # log endpoints
    path(
        'trip-logs/', views.TripLogListCreateView.as_view(), name='triplog-list-create'),
    path(
        'trip-logs/calculate-bulk/', views.TripLogBulkCalculateView.as_view(), name='triplog-calculate-bulk'),
    path(
        'trip-logs/<int:pk>/', views.TripLogDetailView.as_view(), name='triplog-detail'),
    path(
        'trip-logs/<int:pk>/calculate/', views.TripLogCalculationView.as_view(), name='triplog-calculate'
    )
]
