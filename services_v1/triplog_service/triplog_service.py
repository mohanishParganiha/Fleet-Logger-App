"""Business logic for TripLog operations."""
from decimal import Decimal
from datetime import date, datetime
from django.db.models import Sum, F
from fleet.models import TripLog, Vehicle
from .exceptions import TripNotFound, TripAlreadyApproved, InvalidCalculationInput


class TripLogService:
    """Business logic for TripLog operations."""

    @staticmethod
    def approve_trip(trip_id) -> TripLog:
        """Approve and lock a trip log. Idempotent."""
        try:
            trip = TripLog.objects.get(pk=trip_id)
        except TripLog.DoesNotExist:
            raise TripNotFound(f"Trip {trip_id} not found")

        if trip.is_approved:
            raise TripAlreadyApproved("This trip has already been approved and locked")

        trip.is_approved = True
        trip.save()
        return trip

    @staticmethod
    def calculate_single(trip_id, rate: Decimal, calc_type: str) -> dict:
        """Calculate amount for single trip by weight, volume, or distance."""
        try:
            trip = TripLog.objects.get(pk=trip_id)
        except TripLog.DoesNotExist:
            raise TripNotFound(f"Trip {trip_id} not found")

        if calc_type not in ['weight', 'volume', 'distance']:
            raise InvalidCalculationInput("calc_type must be 'weight', 'volume', or 'distance'")

        if rate < 1:
            raise InvalidCalculationInput("rate must be greater than 0")

        if calc_type == 'weight':
            if trip.weight is None:
                raise InvalidCalculationInput("This trip has no weight data")
            quantity_per_trip = trip.weight
            total_quantity = trip.weight * trip.number_of_trips
        elif calc_type == 'volume':
            if trip.volume is None:
                raise InvalidCalculationInput("This trip has no volume data")
            quantity_per_trip = trip.volume
            total_quantity = trip.volume * trip.number_of_trips
        else:
            if trip.distance_traveled is None:
                raise InvalidCalculationInput("This trip has no distance data")
            quantity_per_trip = trip.distance_traveled
            total_quantity = trip.distance_traveled * trip.number_of_trips

        amount = total_quantity * rate

        return {
            "trip_id": trip.id,
            "calc_type": calc_type,
            "rate": rate,
            "quantity_per_trip": float(quantity_per_trip),
            "total_quantity": float(total_quantity),
            "amount": float(amount)
        }

    @staticmethod
    def calculate_bulk(start_date: str, end_date: str, rate: Decimal,
                       calc_type: str, vehicle: str = None) -> dict:
        """Calculate aggregated amount for multiple trips in date range."""
        if calc_type not in ['weight', 'volume', 'distance']:
            raise InvalidCalculationInput("calc_type must be 'weight', 'volume', or 'distance'")

        if rate < 1:
            raise InvalidCalculationInput("rate must be greater than 0")

        try:
            start_date = datetime.fromisoformat(start_date).date()
            end_date = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise InvalidCalculationInput("Invalid date format. Use YYYY-MM-DD")

        if start_date > end_date:
            raise InvalidCalculationInput("start_date cannot exceed end_date")

        trips = TripLog.objects.filter(
            date_time__date__gte=start_date,
            date_time__date__lte=end_date
        )

        if vehicle:
            try:
                vehicle_obj = Vehicle.objects.get(registered_number=vehicle)
                trips = trips.filter(vehicle=vehicle_obj)
            except Vehicle.DoesNotExist:
                raise TripNotFound(f"Vehicle '{vehicle}' not found")

        if calc_type == 'weight':
            total = trips.exclude(weight__isnull=True).aggregate(
                total=Sum(F('weight') * F('number_of_trips'))
            )['total'] or Decimal('0')
            field_name = 'total_weight'
        elif calc_type == 'volume':
            total = trips.exclude(volume__isnull=True).aggregate(
                total=Sum(F('volume') * F('number_of_trips'))
            )['total'] or Decimal('0')
            field_name = 'total_volume'
        else:
            total = trips.exclude(distance_traveled__isnull=True).aggregate(
                total=Sum(F('distance_traveled') * F('number_of_trips'))
            )['total'] or Decimal('0')
            field_name = 'total_distance'

        amount = total * rate

        return {
            "start_date": start_date,
            "end_date": end_date,
            "vehicle": vehicle,
            "total_trips": trips.count(),
            "calc_type": calc_type,
            field_name: float(total),
            "rate": float(rate),
            "total_amount": float(amount)
        }