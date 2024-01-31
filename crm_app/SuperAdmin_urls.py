from django.urls import path , include
from django.conf.urls.static import static
from django.conf import settings
from crm_app.SuperAdminviews import *




urlpatterns = [
    path('logout_user', logout_user,name="logout"),
    path('add_admin/', add_admin,name="add_admin"),
    path('view_admin/', view_admin,name="view_admin"),
    path('delete/<int:id>/', delete_admin, name='delete_admin'),
    path('edit_admin/<int:user_id>/', edit_admin, name='edit_admin'),
    path("crm/dashboard/", DashboardView.as_view() , name='dashboard'),
       
]