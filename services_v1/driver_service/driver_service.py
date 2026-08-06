"""Business logic for Driver operations (placeholder for future use)."""
from fleet.models import Driver


class DriverService:
    """Business logic for Driver operations."""

    @staticmethod
    def get_driver_by_license(license_number: str) -> Driver:
        """Get driver by license number."""
        return Driver.objects.get(license_number=license_number)