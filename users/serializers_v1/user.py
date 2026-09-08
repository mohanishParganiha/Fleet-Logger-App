from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """user serializer that validates the username,email,and password"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'is_active',
            'is_staff', 'is_manager', 'date_created', 'date_updated']
        read_only_fields = ['id', 'is_staff', 'is_active',
                            'is_manager', 'date_created', 'date_updated']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class SetPasswordSerializer(serializers.Serializer):
    """Used by ChangePasswordView. The view resolves the object to
    request.user, so no pk is in the URL and no `user` field is in
    the payload. The serializer only deals with the password."""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get('password', None)
        password_confirm = attrs.get('password_confirm', None)

        if password:
            if password_confirm:
                if attrs['password'] != attrs['password_confirm']:
                    raise serializers.ValidationError(
                        {"password_confirm": "Passwords do not match."})
            else:
                raise serializers.ValidationError(
                    'Confirm Password field cannot be empty')
        else:
            raise serializers.ValidationError('Password field cannot be empty')

        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
