from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    email = serializers.CharField()
    user_id = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_manager = serializers.BooleanField()