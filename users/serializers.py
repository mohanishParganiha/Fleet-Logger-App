from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer (serializers.ModelSerializer):
    """user serializer that validates the username,email,and password"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username',
            'is_staff', 'date_created', 'date_updated']
        read_only_fields = ['id', 'is_staff', 'date_created', 'date_updated']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
