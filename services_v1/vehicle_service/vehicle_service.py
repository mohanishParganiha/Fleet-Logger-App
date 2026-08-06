"""Business logic for Vehicle operations (placeholder for future use)."""
from fleet.models import Vehicle


class VehicleService:
    """Business logic for Vehicle operations."""

    @staticmethod
    def get_vehicle_by_number(registered_number: str) -> Vehicle:
        """Get vehicle by registered number."""
        return Vehicle.objects.get(registered_number=registered_number)