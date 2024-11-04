from rest_framework import serializers

from open_prices.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        # fields = "__all__"
        exclude = ["source"]


class LocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = Location.CREATE_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # with UniqueConstraints, DRF sets some fields as required
        for field in (
            Location.TYPE_OSM_MANDATORY_FIELDS + Location.TYPE_ONLINE_MANDATORY_FIELDS
        ):
            self.fields[field].required = False

    # with UniqueConstraints, DRF wrongly validates.
    # Leave it to the model's save()
    validators = []
