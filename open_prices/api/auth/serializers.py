from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


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
