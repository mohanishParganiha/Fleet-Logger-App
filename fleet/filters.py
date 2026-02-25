"""here we add filters classes for django."""
import django_filters
from .models import TripLog


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
