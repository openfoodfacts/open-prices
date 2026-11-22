from rest_framework import serializers

from open_prices.common import utils
from open_prices.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    osm_brand_logo_url = serializers.CharField(read_only=True)  # from model property

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

    def validate_website_url(self, value):
        # same normalization as Location.cleanup_url(), to find duplicates
        return utils.url_keep_only_domain(value) if value else value

    def validate(self, attrs):
        # run the model validations (except the unique constraints, the view
        # returns the existing location instead), before the duplicate lookup
        Location(**attrs).full_clean(validate_unique=False, validate_constraints=False)
        return attrs


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


class LocationNearbySerializer(LocationSerializer):
    distance_km = serializers.FloatField(read_only=True)


class LocationNearbyParamsSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90, required=True)
    lon = serializers.FloatField(min_value=-180, max_value=180, required=True)
    radius_km = serializers.FloatField(min_value=0, required=True)


class LocationCompareParamsSerializer(serializers.Serializer):
    location_id_a = serializers.IntegerField(required=True)
    location_id_b = serializers.IntegerField(required=True)
    date__gte = serializers.DateField(required=False)
    date__lte = serializers.DateField(required=False)
    price_is_discounted = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )


class LocationCompareSerializer(serializers.Serializer):
    location_a = LocationSerializer()
    location_b = LocationSerializer()
    shared_products = serializers.JSONField()
    total_sum_location_a = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sum_location_b = serializers.DecimalField(max_digits=10, decimal_places=2)
