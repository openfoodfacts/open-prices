from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    access_token = serializers.CharField(required=False, write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        access_token = data.get("access_token")

        if access_token and not (username or password):
            return data

        if username and password and not access_token:
            return data

        raise serializers.ValidationError(
            "Either 'access_token' or both 'username' and 'password' are required."
        )


class SessionResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    is_moderator = serializers.BooleanField()
    access_token = serializers.CharField()
    token_type = serializers.CharField()


class SessionFullSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()
    created = serializers.CharField()
    last_used = serializers.CharField()
