from rest_framework import serializers

from open_prices.moderation.models import Flag


class FlagCreateSerializer(serializers.ModelSerializer):
    # add read_only generic foreign key field
    content_object = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Flag
        fields = Flag.CREATE_FIELDS + ["content_object"]


class FlagSerializer(serializers.ModelSerializer):
    content_type_display = serializers.ReadOnlyField()

    class Meta:
        model = Flag
        fields = "__all__"
