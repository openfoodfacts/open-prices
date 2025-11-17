from rest_framework import serializers

from open_prices.moderation.models import Flag


class FlagCreateSerializer(serializers.ModelSerializer):
    # add read_only generic foreign key field
    content_object = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Flag
        fields = Flag.CREATE_FIELDS + ["content_object"]


class FlagSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = Flag
        fields = "__all__"

    def get_content_type(self, obj):
        return obj.content_type_display.upper()
