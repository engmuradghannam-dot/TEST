from rest_framework import serializers
from .models import CertificationRecord, Partner, MarketplaceApp, CountryLocalization


class CertificationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationRecord
        fields = '__all__'


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'


class MarketplaceAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceApp
        fields = '__all__'


class CountryLocalizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryLocalization
        fields = '__all__'
