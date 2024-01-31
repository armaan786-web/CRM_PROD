from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__

        user = request.user
        if modulename == "crm_app.views" and view_func.__name__ in [
            "chats",
            "get_group_chat_messages",
        ]:
            return None
        if user.is_authenticated:
            if user.user_type == "1":
                if modulename == "crm_app.SuperAdminviews":
                    pass
                elif (
                    modulename == "crm_app.SuperAdminviews"
                    or modulename == "django.views.static"
                ):
                    pass
                elif (
                    modulename == "django.contrib.auth.views"
                    or modulename == "django.contrib.admin.sites"
                ):
                    pass
                else:
                    return HttpResponseRedirect(reverse("dashboard"))

            elif user.user_type == "2":
                if modulename == "crm_app.AdminViews":
                    pass
                elif (
                    modulename == "crm_app.AdminViews"
                    or modulename == "django.views.static"
                ):
                    pass
                else:
                    return HttpResponseRedirect(reverse("admin_dashboard"))

            elif user.user_type == "3":
                if modulename == "crm_app.EmployeeViews":
                    pass
                elif (
                    modulename == "crm_app.EmployeeViews"
                    or modulename == "django.views.static"
                ):
                    pass
                else:
                    return HttpResponseRedirect(reverse("employee_dashboard"))

            elif user.user_type in ["4", "5"]:
                if modulename in ["crm_app.AgentViews", "django.views.static"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("agent_dashboard"))

            elif user.user_type == "3":
                if modulename == "crm_app.EmployeeViews":
                    pass
                else:
                    return HttpResponseRedirect(reverse("employee_dashboard"))

            else:
                return HttpResponseRedirect(reverse("login"))
