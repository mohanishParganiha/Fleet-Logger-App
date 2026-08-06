"""Fleet API v1 serializers package."""
from .auth import LoginRequestSerializer, LoginResponseSerializer
from .vehicle import VehicleSerializer
from .driver import DriverSerializer
from .triplog import (
    TripLogSerializer,
    TripCalculationInputSerializer,
    BulkCalculationInputSerializer
)

__all__ = [
    'LoginRequestSerializer', 'LoginResponseSerializer',
    'VehicleSerializer', 'DriverSerializer',
    'TripLogSerializer', 'TripCalculationInputSerializer', 'BulkCalculationInputSerializer',
]