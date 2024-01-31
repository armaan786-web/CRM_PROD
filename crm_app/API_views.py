from rest_framework import viewsets
from .models import (
    Booking,
    FrontWebsiteEnquiry,
    VisaCountry,
    VisaCategory,
    Package,
    Enquiry,
)
from .serializers import (
    BookingSerializer,
    FrontWebsiteSerializer,
    VisaCategorySerializer,
    VisaCountrySerializer,
    ProductSerializer,
    EnquirySerializer,
)
from rest_framework.viewsets import ViewSet, ModelViewSet


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class FrontWebsite(ModelViewSet):
    queryset = FrontWebsiteEnquiry.objects.all()
    serializer_class = FrontWebsiteSerializer


class apiVisaCountry(ModelViewSet):
    queryset = VisaCountry.objects.all()
    serializer_class = VisaCountrySerializer


class apiVisaCategory(ModelViewSet):
    queryset = VisaCategory.objects.all()
    serializer_class = VisaCategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.filter(approval="True")
    serializer_class = ProductSerializer


class EnquiryViewSet(viewsets.ModelViewSet):
    # queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer

    def get_queryset(self):
        contact = self.request.query_params.get("contact")
        queryset = Enquiry.objects.filter(contact=contact)
        return queryset
