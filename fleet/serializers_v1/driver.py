from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from fleet.models import Driver, Vehicle
from users.serializers_v1 import RegisterSerializer
User = get_user_model()


class DriverCreateSerializer(serializers.ModelSerializer):
    # required=True ensures user account details must be provided during creation
    user = RegisterSerializer(required=True)

    primary_vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number'
    )

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
        read_only_fields = ['id', 'status', 'date_created', 'date_updated']

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


class DriverSerializer(serializers.ModelSerializer):
    """ Serializer for retrieve and delete driver fields by admin/manager"""
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='id'
    )
    primary_vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number'
    )

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

        read_only_fields = ['id', 'user', 'date_created', 'date_updated']


class DriverUpdateSerializer(serializers.ModelSerializer):
    """ Serializer for update driver fields by admin/manager"""

    primary_vehicle = serializers.SlugRelatedField(
        queryset=Vehicle.objects.all(),
        slug_field='registered_number'
    )

    class Meta:
        model = Driver

        fields = [
            'id',
            'name',
            'phone_number',
            'license_number',
            'primary_vehicle',
            'status',
            'date_created',
            'date_updated'
        ]

        read_only_fields = ['id', 'date_created', 'date_updated']


class DriverSelfSerializer(serializers.ModelSerializer):
    """used to retrieve and update driver fields by drivers"""
    user = serializers.SlugRelatedField(
        slug_field='id',
        read_only=True
    )
    primary_vehicle = serializers.SlugRelatedField(
        slug_field='registered_number',
        read_only=True
    )

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

        read_only_fields = ['id', 'user', 'primary_vehicle',
                            'license_number',  'status', 'date_created', 'date_updated']
