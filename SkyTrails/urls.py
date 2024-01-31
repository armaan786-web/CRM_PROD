from django.contrib import admin
from django.urls import path, include
from crm_app import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from django.urls import re_path
from crm_app.API_views import *
from django.views.generic import TemplateView
from crm_app import views
from rest_framework.routers import DefaultRouter
from crm_app import API_views

router = DefaultRouter()
router.register("Product", API_views.ProductViewSet, basename="product")
router.register("Enqury", API_views.EnquiryViewSet, basename="enquiry")


urlpatterns = (
    [
        re_path("media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path("static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
        path("__debug__/", include("debug_toolbar.urls")),
        path("api/", include(router.urls), name="api"),
        path("admin/", admin.site.urls),
        path("Signup/", views.agent_signup, name="agent_signup"),
        path("", views.CustomLoginView, name="login"),
        path("OTP/", views.verify_otp, name="verify_otp"),
        path("ResendOTP/", views.resend_otp, name="resend_otp"),
        path("forgot/Password", views.forgot_psw, name="forgot_psw"),
        path("Forget/Verify/OTP/", views.forget_otp, name="forget_otp"),
        path("ResetPassword/", views.reset_psw, name="reset_psw"),
        path("Admin/", include("crm_app.Admin_urls")),
        path("Agent/", include("crm_app.Agent_urls")),
        path("Employee/", include("crm_app.Employee_urls")),
        path("SuperAdmin/", include("crm_app.SuperAdmin_urls")),
        ########################## API URLS ##############################################
        path(
            "enquiry_form/",
            BookingViewSet.as_view({"get": "list", "post": "create"}),
            name="enquiry",
        ),
        path("FrontWebsite/", FrontWebsite.as_view({"get": "list", "post": "create"})),
        path("Api/VisaCountry/", apiVisaCountry.as_view({"get": "list"})),
        path("Api/VisaCategory/", apiVisaCategory.as_view({"get": "list"})),
        path("Chat/", views.chats, name="chat"),
        path(
            "get_group_chat_messages/",
            views.get_group_chat_messages,
            name="get_group_chat_messages",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
handler404 = "crm_app.views.Error404"
