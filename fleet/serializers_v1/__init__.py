"""Fleet API v1 serializers package."""
# from .auth import LoginRequestSerializer, LoginResponseSerializer
from .auth import CustomTokenObtainPairSerializer
from .vehicle import VehicleSerializer
from .driver import DriverCreateSerializer, DriverSerializer, DriverSelfSerializer, DriverUpdateSerializer
from .triplog import (
    TripLogSerializer,
    TripCalculationInputSerializer,
    BulkCalculationInputSerializer
)

__all__ = [
    # 'LoginRequestSerializer', 'LoginResponseSerializer',
    'CustomTokenObtainPairSerializer',
    'VehicleSerializer', 'DriverCreateSerializer', 'DriverSerializer', 'DriverSelfSerializer', 'DriverUpdateSerializer',
    'TripLogSerializer', 'TripCalculationInputSerializer', 'BulkCalculationInputSerializer',
]
