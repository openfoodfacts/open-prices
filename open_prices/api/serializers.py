from rest_framework import serializers


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
