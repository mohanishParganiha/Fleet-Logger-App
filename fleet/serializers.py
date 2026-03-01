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


class TripLogSerializer(serializers.ModelSerializer):
    vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number'
    )

    driver = serializers.SlugRelatedField(
        queryset=Driver.objects.all(),
        slug_field='license_number'
    )

    def validate_number_of_trips(self, value):
        """check if number of trips should be greater than equal to 0"""
        if value < 0:
            raise serializers.ValidationError(
                'number of trips must be greater than equal to 0')
        return value

    def validate_weight(self, value):
        """check if number of trips should be greate than equal to 0"""
        if value < 0:
            raise serializers.ValidationError(
                'weight must be greater than equal to 0')
        return value

    def validate_distance_traveled(self, value):
        """check if number of trips should be greate than equal to 0"""
        if value < 0:
            raise serializers.ValidationError(
                'distance traveled must be greater than equal to 0')
        return value

    class Meta:
        model = TripLog
        fields = '__all__'
