"""here we add filters classes for django."""
import django_filters
from .models import TripLog, Vehicle, Driver


class TripLogFilter(django_filters.FilterSet):
    """this filter filters data in logs with "range of dates" and/or "vehicle registerd number and/or "driver licese number"."""
    start_date = django_filters.DateFilter(
        field_name='date_time__date', lookup_expr='gte', label='START DATE')
    end_date = django_filters.DateFilter(
        field_name='date_time__date', lookup_expr='lte', label='END DATE')
    vehicle = django_filters.CharFilter(
        field_name='vehicle__registered_number', label='VEHICLE REGISTERED NUMBER')
    driver = django_filters.CharFilter(
        field_name='driver__license_number', label='DRIVER LICENSE NUMBER')

    class Meta:
        model = TripLog
        fields = []


class VehicleFilter(django_filters.FilterSet):
    """this filter filters data in vehicles with  models and/or registered number and/or date created and/or status """
    model = django_filters.CharFilter(
        field_name='model', label='MODEL'
    )
    registered_number = django_filters.CharFilter(
        field_name='registered_number', label='REGISTERED NUMBER'
    )
    date_created = django_filters.DateFilter(
        field_name='date_created', label='DATE CREATED'
    )
    status = django_filters.CharFilter(
        field_name='status', label='STATUS'
    )

    class Meta:
        model = Vehicle
        fields = []


class DriverFilter(django_filters.FilterSet):
    """this filter filters data in driver with """
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains', label='NAME'
    )
    license_number = django_filters.CharFilter(
        field_name='license_number', label='LICESE NUMBER'
    )
    status = django_filters.CharFilter(
        field_name='status', label='STATUS'
    )
    date_created = django_filters.DateFilter(
        field_name='date_created', label='DATE CRAETED'
    )

    class Meta:
        model = Driver
        fields = []
