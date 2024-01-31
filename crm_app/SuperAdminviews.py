from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Admin, CustomUser
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .SMSAPI.whatsapp_api import send_whatsapp_message, send_sms_message
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .Email.email_utils import send_congratulatory_email


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")


class DashboardView(TemplateView):
    template_name = "SuperAdmin/Dashboard/dashboard.html"


def add_admin(request):
    if request.method == "POST":
        department = request.POST.get("department")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = request.POST.get("password")
        user_type = "2"

        try:
            if CustomUser.objects.filter(username=email).exists():
                messages.warning(request, f"{email} Admin already exists")
                return redirect("add_admin")

            if CustomUser.objects.filter(email=email).exists():
                messages.warning(request, f"{email} This email already exists")
                return redirect("add_admin")

            user = CustomUser.objects.create_user(
                username=email,
                first_name=firstname,
                last_name=lastname,
                email=email,
                password=password,
                user_type="2",
            )

            user.admin.department = department
            user.admin.contact_no = contact
            user.save()
            subject = "Congratulations! Your Account is Created"
            # message = (
            #     f"Hello {firstname} {lastname},\n\n"
            #     f"Welcome to SSDC \n\n"
            #     f"Congratulations! Your account has been successfully created as an admin.\n\n"
            #     f" Your id is {email} and your password is {password}.\n\n"
            #     f" go to login : https://crm.theskytrails.com/ \n\n"
            #     f"Thank you for joining us!\n\n"
            #     f"Best regards,\nThe Sky Trails"
            # )  # Customize this message as needed

            html_message = render_to_string(
                "email_template.html",
                {
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "password": password,
                    "user_type": "2",
                },
            )
            plain_message = strip_tags(html_message)

            mobile = contact
            message = (
                f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                f" Hello {firstname} {lastname}, \n\n"
                f" Welcome to Sky Trails! Your admin account is ready to roll. \n\n"
                f" Account Details: \n\n"
                f" Email: {email} \n\n"
                f" Password: {password} \n\n"
                f" Login Here: 🚀 https://crm.theskytrails.com/ \n\n"
                f" Excited to have you on board! Explore our specialized services in work permits, migration support, and skill training. Also, check out our travel services at 🌐 www.thesktrails.com. \n\n"
                f" Stay connected on social media: \n\n"
                f" 📘 https://www.facebook.com/skytrails.skill.development.center/ \n\n"
                f" 🐦 https://twitter.com/TheSkytrails \n\n"
                f" 🤝 https://www.linkedin.com/company/theskytrailsofficial \n\n"
                f" 📸 https://www.instagram.com/skytrails_ssdc/ \n\n"
                f" Got questions? Need assistance? We're here for you! \n\n"
                f" Best, \n\n"
                f" The Sky Trails Team \n\n"
            )
            response = send_whatsapp_message(mobile, message)
            if response.status_code == 200:
                pass
            else:
                pass

            send_congratulatory_email(firstname, lastname, email, password, user_type)
            messages.success(
                request,
                f"{email} Created Successfully and Congratulatory Email Sent!!!",
            )
            return redirect("view_admin")
        except Exception as e:
            messages.warning(request, "Something is Wrong Try Again")

    return render(request, "SuperAdmin/Admin Management/addadmin.html")


def view_admin(request):
    admin = Admin.objects.all()
    context = {"admin": admin}

    return render(request, "SuperAdmin/Admin Management/adminlist.html", context)


def edit_admin(request, user_id):
    admin = get_object_or_404(Admin, users_id=user_id)

    if request.method == "POST":
        department = request.POST.get("department")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")

        try:
            if (
                CustomUser.objects.filter(email=email)
                .exclude(id=admin.users.id)
                .exists()
            ):
                messages.warning(request, f"{email} This email already exists")
                return redirect("edit_admin", user_id=user_id)

            admin.users.username = email
            admin.users.first_name = firstname
            admin.users.last_name = lastname
            admin.users.email = email
            admin.users.save()

            admin.department = department
            admin.contact_no = contact
            admin.save()

            messages.success(request, f"{email} Updated Successfully")
            return redirect("view_admin")
        except Exception as e:
            messages.warning(request, "Something went wrong. Please try again.")
            print(e)

    return render(
        request, "SuperAdmin/Admin Management/editadmin.html", {"admin": admin}
    )


def delete_admin(request, id):
    try:
        admin = get_object_or_404(Admin, users_id=id)
        admin.delete()
    except Admin.DoesNotExist:
        pass
    except Exception as e:
        pass
    return redirect("view_admin")
