from rest_framework import serializers

class AddressSearchSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    radius_km = serializers.FloatField(min_value=0.1, max_value=50, default=1.0)
    address_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        default=['house', 'apartment', 'residential']
    )
    limit = serializers.IntegerField(min_value=1, max_value=500, default=100)
