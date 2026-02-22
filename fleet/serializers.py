from rest_framework import serializers
from .models import Truck, Driver, TripLog


# simple truck serializer
class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'


class TripLogSerializer(serializers.ModelSerializer):
    truck = serializers.SlugRelatedField(
        queryset=Truck.objects.all(),
        slug_field='registered_number'
    )

    driver = serializers.SlugRelatedField(
        queryset=Driver.objects.all(),
        slug_field='license_number'
    )

    class Meta:
        model = TripLog
        fields = '__all__'
