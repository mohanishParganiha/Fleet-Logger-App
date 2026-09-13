"""Fleet API v1 views package."""
from .auth import CustomTokenObtainPairView, CustomTokenRefreshView, CustomLogoutView
from .vehicle import VehicleListCreateView, VehicleDetailView
from .driver import DriverListCreateView, DriverDetailView, DriverMeView
from .triplog import (
    TripLogListCreateView, TripLogDetailView,
    TripLogApproveView, TripLogCalculationView, TripLogBulkCalculateView
)

__all__ = [
    'CustomTokenObtainPairView', 'CustomTokenRefreshView', 'CustomLogoutView',
    'VehicleListCreateView', 'VehicleDetailView',
    'DriverListCreateView', 'DriverDetailView', 'DriverMeView',
    'TripLogListCreateView', 'TripLogDetailView',
    'TripLogApproveView', 'TripLogCalculationView', 'TripLogBulkCalculateView',
]
