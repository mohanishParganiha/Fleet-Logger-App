from rest_framework import serializers, status
from django.utils import timezone
from datetime import timedelta
from fleet.models import Vehicle, TripLog


def validate_negative_values(value):
    if value < 0:
        raise serializers.ValidationError(
            'value must be greater than equal to 0')
    return value


class TripCalculationInputSerializer(serializers.Serializer):
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    calc_type = serializers.CharField()


class BulkCalculationInputSerializer(serializers.Serializer):
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    calc_type = serializers.CharField()
    vehicle = serializers.CharField(required=False)


class TripLogSerializer(serializers.ModelSerializer):
    vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number',
        required=False,
        allow_null=True
    )

    driver = serializers.SlugRelatedField(
        slug_field='license_number',
        read_only=True
    )

    driver_name = serializers.CharField(source='driver.name', read_only=True)

    number_of_trips = serializers.IntegerField(
        validators=[validate_negative_values])

    weight = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True, validators=[validate_negative_values], required=False)

    volume = serializers.DecimalField(
        max_digits=5, decimal_places=2, allow_null=True, validators=[validate_negative_values], required=False)

    distance_traveled = serializers.DecimalField(
        max_digits=5, decimal_places=2, allow_null=True, validators=[validate_negative_values], required=False)

    diesel_fill = serializers.DecimalField(
        max_digits=6, decimal_places=2, allow_null=True, validators=[validate_negative_values], required=False)

    is_approved = serializers.BooleanField(read_only=True)

    last_reason_to_change = serializers.CharField(required=False)

    class Meta:
        model = TripLog
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            return attrs
        user = request.user

        # check if the method is put/patch , then check if last_reason_to_change is set
        if request.method in ['PUT', 'PATCH'] and not attrs.get('last_reason_to_change'):
            raise serializers.ValidationError(
                detail="You must give reason to update the trip logs",
                code=status.HTTP_400_BAD_REQUEST
            )

        # check if weight or volume are present , both cannot be empty at once
        if self.instance and request.method == 'PATCH':
            weight = attrs.get('weight', self.instance.weight)
            volume = attrs.get('volume', self.instance.volume)
        else:
            weight = attrs.get('weight')
            volume = attrs.get('volume')

        if not weight and not volume:
            raise serializers.ValidationError(
                detail="Both Weight and Volume cannot be emtpy",
                code=status.HTTP_400_BAD_REQUEST
            )

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

            # second check , check for time window of 2hrs
            time_elapsed = timezone.now() - instance.date_created
            if time_elapsed > timedelta(hours=2):
                raise serializers.ValidationError(
                    detail="More than 2 hours has passed, cannot make any changes. Contact Manager/Admin",
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
        data = super().to_representation(instance)

        vehicle_obj = instance.vehicle
        if not vehicle_obj and instance.driver:
            vehicle_obj = getattr(instance.driver, 'primary_vehicle', None)

        data['vehicle'] = {
            'id': vehicle_obj.id,
            'registered_number': vehicle_obj.registered_number
        } if vehicle_obj else None

        data['driver'] = {
            'id': instance.driver.id,
            'license_number': instance.driver.license_number
        } if instance.driver else None

        data.pop('vehicle_id', None)
        data.pop('driver_id', None)
        data.pop('driver_name', None)

        return data
