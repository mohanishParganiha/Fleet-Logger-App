"""Fleet API v1 serializers package."""
from .auth import LoginRequestSerializer, LoginResponseSerializer
from .vehicle import VehicleSerializer
from .driver import DriverCreateSerializer, DriverSerializer, DriverSelfSerializer
from .triplog import (
    TripLogSerializer,
    TripCalculationInputSerializer,
    BulkCalculationInputSerializer
)

__all__ = [
    'LoginRequestSerializer', 'LoginResponseSerializer',
    'VehicleSerializer', 'DriverCreateSerializer', 'DriverSerializer', 'DriverSelfSerializer',
    'TripLogSerializer', 'TripCalculationInputSerializer', 'BulkCalculationInputSerializer',
]
