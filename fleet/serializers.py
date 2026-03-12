from rest_framework import serializers
from .models import Vehicle, Driver, TripLog


# simple Vehicle serializer
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'


def validate_negative_values(value):
    if value < 0:
        raise serializers.ValidationError(
            'value must be greater than equal to 0')
    return value


class TripLogSerializer(serializers.ModelSerializer):
    vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number'
    )
    vehicle_id = serializers.IntegerField(source='vehicle.id', read_only=True)

    driver = serializers.SlugRelatedField(
        queryset=Driver.objects.all(),
        slug_field='license_number'
    )
    driver_id = serializers.IntegerField(source='driver.id', read_only=True)
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    number_of_trips = serializers.IntegerField(
        validators=[validate_negative_values])

    weight = serializers.DecimalField(
        max_digits=10, decimal_places=2, validators=[validate_negative_values], required=False)

    distance_traveled = serializers.DecimalField(
        max_digits=5, decimal_places=2, validators=[validate_negative_values], required=False)

    diesel_fill = serializers.DecimalField(
        max_digits=6, decimal_places=2, validators=[validate_negative_values], required=False)

    class Meta:
        model = TripLog
        fields = '__all__'
