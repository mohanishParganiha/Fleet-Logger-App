from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework import serializers


# class LoginRequestSerializer(serializers.Serializer):
#     email = serializers.CharField(required=True)
#     password = serializers.CharField(required=True, write_only=True)


# class LoginResponseSerializer(serializers.Serializer):
#     email = serializers.CharField()
#     user_id = serializers.CharField()
#     is_staff = serializers.BooleanField()
#     is_manager = serializers.BooleanField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 1. This authenticates the user against the DB and generates the default tokens
        data = super().validate(attrs)

        # 2. Grab the authenticated user model instance from the database
        user = self.user

        # 3. Inject whatever user metadata you want into the JSON response body
        data['user'] = {  # type: ignore
            'id': user.id,  # type: ignore
            'username': user.username,  # type: ignore
            'email': user.email,  # type: ignore
            'is_manager': user.is_manager,  # type: ignore
            'is_staff': user.is_staff,  # type: ignore
            # Add any other custom profile fields here
        }

        return data
