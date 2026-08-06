from rest_framework import serializers
from django.db import transaction
from fleet.models import Driver
from users.serializers_v1 import RegisterSerializer


class DriverSerializer(serializers.ModelSerializer):
    # required=True ensures user account details must be provided during creation
    user = RegisterSerializer(required=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            'user',
            'name',
            'phone_number',
            'license_number',
            'primary_vehicle',
            'status',
            'date_created',
            'date_updated'
        ]
        read_only_fields = ['id', 'date_created', 'date_updated']

    def create(self, validated_data):
        # 1. Extract the clean, pre-validated user dictionary data
        user_data = validated_data.pop('user')

        with transaction.atomic():
            # 2. Call the RegisterSerializer explicitly to handle the password hashing
            user_serializer = RegisterSerializer()
            user = user_serializer.create(validated_data=user_data)

            # 3. Create the driver with the completed user instance
            driver = Driver.objects.create(user=user, **validated_data)

        return driver