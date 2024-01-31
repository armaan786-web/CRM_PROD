from rest_framework import serializers
from .models import (
    Booking,
    FrontWebsiteEnquiry,
    VisaCountry,
    VisaCategory,
    Package,
    Enquiry,
)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class VisaCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaCountry
        fields = [
            "id",
            "country",
        ]


class VisaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaCategory
        fields = ["id", "category"]


class FrontWebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontWebsiteEnquiry
        fields = [
            "name",
            "email",
            "appointment_date",
            "phone",
            "country_name",
            "category_name",
            "message",
            "image",
        ]


class ProductSerializer(serializers.ModelSerializer):
    visa_country = VisaCountrySerializer()

    class Meta:
        model = Package
        fields = "__all__"


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = "__all__"
