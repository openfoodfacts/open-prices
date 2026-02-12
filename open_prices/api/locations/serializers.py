from rest_framework import serializers

from open_prices.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"


class LocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = Location.CREATE_FIELDS
        # https://github.com/encode/django-rest-framework/issues/7173
        # with UniqueConstraints, DRF wrongly validates.
        # Leave it to the model's save()
        validators = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # with UniqueConstraints, DRF sets some fields as required
        for field in (
            Location.TYPE_OSM_MANDATORY_FIELDS + Location.TYPE_ONLINE_MANDATORY_FIELDS
        ):
            self.fields[field].required = False
            self.fields[field].validators = []


class CountrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country_code_2 = serializers.CharField()
    osm_name = serializers.CharField()
    location_count = serializers.IntegerField()
    price_count = serializers.IntegerField()


class CountryCitySerializer(serializers.Serializer):
    osm_name = serializers.CharField()
    country_code_2 = serializers.CharField()
    location_count = serializers.IntegerField()
    price_count = serializers.IntegerField()


class LocationCompareSerializer(serializers.Serializer):
    location_a = LocationSerializer()
    location_b = LocationSerializer()
    shared_products = serializers.ListField(child=serializers.CharField())
    total_sum_location_a = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sum_location_b = serializers.DecimalField(max_digits=10, decimal_places=2)
