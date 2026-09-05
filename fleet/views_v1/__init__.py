"""Fleet API v1 views package."""
from .auth import LoginView, LogoutView
from .vehicle import VehicleListCreateView, VehicleDetailView
from .driver import DriverListCreateView, DriverDetailView, DriverMeView
from .triplog import (
    TripLogListCreateView, TripLogDetailView,
    TripLogApproveView, TripLogCalculationView, TripLogBulkCalculateView
)

__all__ = [
    'LoginView', 'LogoutView',
    'VehicleListCreateView', 'VehicleDetailView',
    'DriverListCreateView', 'DriverDetailView', 'DriverMeView',
    'TripLogListCreateView', 'TripLogDetailView',
    'TripLogApproveView', 'TripLogCalculationView', 'TripLogBulkCalculateView',
]
