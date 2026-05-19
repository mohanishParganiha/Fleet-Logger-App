from rest_framework import serializers, status
from .models import Vehicle, Driver, TripLog
from django.utils import timezone
from datetime import timedelta


# simple login serializer

class LoginRequestSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    email = serializers.CharField()
    user_id = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_manager = serializers.BooleanField()


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
        slug_field='registered_number',
        required=False,
        allow_null=True
    )

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

    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = TripLog
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            return attrs
        user = request.user

        # Determine the driver instance for this log execution
        driver = attrs.get('driver') or (
            self.instance.driver if self.instance else None)

        # --- NEW FLEXIBLE LOGIC FOR VEHICLE OVERRIDE ---
        # If the frontend did NOT explicitly pass a vehicle string, default it to the driver's primary vehicle
        if 'vehicle' not in attrs:
            # Assumes your new field on Driver model is named 'primary_vehicle'
            if driver and getattr(driver, 'primary_vehicle', None):
                attrs['vehicle'] = driver.primary_vehicle
            else:
                attrs['vehicle'] = None

        is_user_driver = not getattr(user, 'is_manager', False) and not (
            user and user.is_staff)

        if self.instance and is_user_driver:
            instance = self.instance

            # first check , if log is approved by manager/admin.
            if getattr(instance, 'is_approved', False):
                raise serializers.ValidationError(
                    detail="Cannot make changes, trip is already approved.",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # second check , check for tiem window of 2hrs
            time_elapsed = timezone.now() - instance.date_created
            if time_elapsed > timedelta(seconds=1.0):
                raise serializers.ValidationError(
                    detail="More than 2 hours has passed , cannot make any changes. Contact Manager/Admin",
                    code=status.HTTP_400_BAD_REQUEST
                )

            if 'vehicle' in attrs and attrs['vehicle'] != instance.vehicle:
                raise serializers.ValidationError(
                    {'vehicle': 'Drivers cannot change the assigned vehicle after creation'})
            if 'driver' in attrs and attrs['driver'] != instance.driver:
                raise serializers.ValidationError(
                    {'vehicle': 'Drivers cannot change the assigned driver after creation'})
        return attrs

    def to_representation(self, instance):
        """Outputs rich nested structures back to the frontend for form loading/view"""
        data = super().to_representation(instance)

        vehicle_obj = instance.vehicle
        if not vehicle_obj or not instance.driver or not getattr(instance.driver, 'primary_vehicle', None):
            vehicle_obj = instance.driver.primary_vehicle

        data['vehicle'] = VehicleSerializer(
            vehicle_obj, context=self.context).data if vehicle_obj else None
        data['driver'] = DriverSerializer(
            instance.driver, context=self.context).data if instance.driver else None

        data.pop('vehicle_id', None)
        data.pop('driver_id', None)
        data.pop('driver_name', None)

        return data
