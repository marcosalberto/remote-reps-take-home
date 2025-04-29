from rest_framework import serializers
from .models import Settings, Brand, Ad

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    ads = AdSerializer(many=True, read_only=True)

    class Meta:
        model = Brand
        fields = '__all__'