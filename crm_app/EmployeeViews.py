from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    TemplateView,
)
from .forms import *
from django.urls import reverse_lazy
from django.db.models import Prefetch
import requests
from .SMSAPI.whatsapp_api import send_whatsapp_message, send_sms_message
from django.core.mail import send_mail
from datetime import datetime
from django.utils import timezone

from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views import View
import pandas as pd
from .Email.email_utils import send_congratulatory_email
from django.db.models.functions import TruncMonth
from django.db.models import Case, When, Value, IntegerField
from django.http import JsonResponse
from .notifications import (
    create_notification,
    send_notification,
    assign_notification,
    create_notification_agent,
    assignop_notification,
    create_notification_outsourceagent,
    send_notification_admin,
    create_admin_notification,
)


def employee_query_list(request):
    user = request.user
    dep = user.employee.department
    context = {"dep": dep}
    return render(request, "Employee/Queries/querieslist.html", context)


def employee_pending_query(request):
    user = request.user
    dep = user.employee.department
    context = {"dep": dep}
    return render(request, "Employee/Queries/pending_query.html", context)


def employee_followup_list(request):
    user = request.user
    dep = user.employee.department
    context = {"dep": dep}
    return render(request, "Employee/FollowUp/followup_list.html", context)


# ----------------------------------------------------------------


class employee_dashboard(LoginRequiredMixin, TemplateView):
    template_name = "Employee/Dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enq_count = 0
        enq_enrolled_count = 0

        agent_count = Agent.objects.filter(
            Q(registerdby=self.request.user)
            | Q(assign_employee=self.request.user.employee)
        ).count

        outsourceagent_count = OutSourcingAgent.objects.filter(
            registerdby=self.request.user
        ).count

        leadpending_count = Enquiry.objects.filter(
            Q(lead_status="Active") | Q(lead_status="PreEnrolled"),
            created_by=self.request.user,
        ).count()

        leadcomplete_count = Enquiry.objects.filter(
            lead_status="Delivery", created_by=self.request.user
        ).count()

        leadaccept_count = Enquiry.objects.filter(
            lead_status="Enrolled",
            created_by=self.request.user,
        ).count()

        leadinprocess_count = Enquiry.objects.filter(
            Q(lead_status="Inprocess") | Q(lead_status="Ready To Submit"),
            created_by=self.request.user,
        ).count()

        appoint_count = Enquiry.objects.filter(
            Q(lead_status="Appointment") | Q(lead_status="Ready To Collection"),
            created_by=self.request.user,
        ).count()

        lead_count = Enquiry.objects.filter(created_by=self.request.user).count()

        leadnew_count = Enquiry.objects.filter(
            lead_status="New Lead", created_by=self.request.user
        ).count()

        resultlead_count = Enquiry.objects.filter(
            lead_status="Result", created_by=self.request.user
        ).count()
        package = Package.objects.filter(approval="True").order_by("-last_updated_on")[
            :10
        ]

        active_users = CustomUser.objects.filter(is_logged_in=True).count()
        active_employee = CustomUser.objects.filter(user_type="3", is_logged_in=True)
        active_agent = CustomUser.objects.filter(
            user_type__in=["4", "5"], is_logged_in=True
        )

        story = SuccessStory.objects.all()
        latest_news = News.objects.filter(employee=True).order_by("-created_at")[:10]

        user = self.request.user
        if user.user_type == "4":
            agent = Agent.objects.get(users=user)
            context["agent"] = agent

        if user.user_type == "5":
            outagent = OutSourcingAgent.objects.get(users=user)
            context["agent"] = outagent

        dep = user.employee.department

        if dep == "Presales":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(lead_status="Enrolled", assign_to_employee=user.employee)
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_employee=user.employee) | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        elif dep == "Sales":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(lead_status="Enrolled", assign_to_sales_employee=user.employee)
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_sales_employee=user.employee) | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        elif dep == "Documentation":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_documentation_employee=user.employee,
                    )
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_documentation_employee=user.employee)
                    | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        elif dep == "HR":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_documentation_employee=user.employee,
                    )
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_documentation_employee=user.employee)
                    | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        elif dep == "Visa Team":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_visa_team_employee=user.employee,
                    )
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_visa_team_employee=user.employee) | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        elif dep == "Assesment":
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_assesment_employee=user.employee,
                    )
                    | Q(lead_status="Enrolled", created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if enrolled_monthly_counts.exists():
                enq_enrolled_count = enrolled_monthly_counts[0]["count"]

            all_enq = (
                Enquiry.objects.filter(
                    Q(assign_to_assesment_employee=user.employee) | Q(created_by=user)
                )
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        todo = Todo.objects.filter(user=self.request.user).order_by("-id")
        context["dep"] = dep

        import requests

        url = "https://back.theskytrails.com/skyTrails/international/getAll"

        response = requests.get(url)

        if response.status_code == 200:
            # The API call was successful, and you can access the data using response.json()
            data = response.json()

        else:
            # The API call failed, and you can print the status code and any error message
            print(f"Error: {response.status_code}, {response.text}")

        context["leadcomplete_count"] = leadcomplete_count
        context["leadaccept_count"] = leadaccept_count
        context["leadpending_count"] = leadpending_count
        context["lead_count"] = lead_count
        context["leadnew_count"] = leadnew_count
        context["package"] = package
        context["agent_count"] = agent_count
        context["outsourceagent_count"] = outsourceagent_count
        context["enrolled_monthly_counts"] = enrolled_monthly_counts
        context["all_enq"] = all_enq
        context["enq_count"] = enq_count
        context["enq_enrolled_count"] = enq_enrolled_count
        context["story"] = story
        context["latest_news"] = latest_news
        context["todo"] = todo
        context["data"] = data
        context["active_users"] = active_users
        context["active_employee"] = active_employee
        context["active_agent"] = active_agent
        context["appoint_count"] = appoint_count
        context["leadinprocess_count"] = leadinprocess_count
        context["resultlead_count"] = resultlead_count

        # context["enq_count"] = enq_count

        return context


class emp_Enquiry1View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm1()
        user = request.user
        dep = user.employee.department
        context = {"dep": dep, "form": form}
        return render(request, "Employee/Enquiry/lead1.html", context)

    def post(self, request):
        form = EnquiryForm1(request.POST)
        if form.is_valid():
            cleaned_data = {
                "FirstName": form.cleaned_data["FirstName"],
                "LastName": form.cleaned_data["LastName"],
                "email": form.cleaned_data["email"],
                "contact": form.cleaned_data["contact"],
                "Dob": form.cleaned_data["Dob"].strftime("%Y-%m-%d"),
                "Gender": form.cleaned_data["Gender"],
                "Country": form.cleaned_data["Country"],
                "passport_no": form.cleaned_data["passport_no"],
            }
            request.session["enquiry_form1"] = cleaned_data
            return redirect("emp_enquiry_form2")

        return render(
            request,
            "Admin/Enquiry/lead2.html",
            {"form": form},
        )


class emp_Enquiry2View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm2()
        user = request.user
        dep = user.employee.department
        context = {"dep": dep, "form": form}
        return render(request, "Employee/Enquiry/lead2.html", context)

    def post(self, request):
        form = EnquiryForm2(request.POST)
        if form.is_valid():
            # Retrieve personal details from session
            enquiry_form1 = request.session.get("enquiry_form1", {})

            cleaned_data = {
                "spouse_name": form.cleaned_data["spouse_name"],
                "spouse_no": form.cleaned_data["spouse_no"],
                "spouse_email": form.cleaned_data["spouse_email"],
                "spouse_passport": form.cleaned_data["spouse_passport"],
                "spouse_relation": form.cleaned_data["spouse_relation"],
                "spouse_name1": form.cleaned_data["spouse_name1"],
                "spouse_no1": form.cleaned_data["spouse_no1"],
                "spouse_email1": form.cleaned_data["spouse_email1"],
                "spouse_passport1": form.cleaned_data["spouse_passport1"],
                "spouse_relation1": form.cleaned_data["spouse_relation1"],
                "spouse_name2": form.cleaned_data["spouse_name2"],
                "spouse_no2": form.cleaned_data["spouse_no2"],
                "spouse_email2": form.cleaned_data["spouse_email2"],
                "spouse_passport2": form.cleaned_data["spouse_passport2"],
                "spouse_relation2": form.cleaned_data["spouse_relation2"],
                "spouse_name3": form.cleaned_data["spouse_name3"],
                "spouse_no3": form.cleaned_data["spouse_no3"],
                "spouse_email3": form.cleaned_data["spouse_email3"],
                "spouse_passport3": form.cleaned_data["spouse_passport3"],
                "spouse_relation3": form.cleaned_data["spouse_relation3"],
                "spouse_name4": form.cleaned_data["spouse_name4"],
                "spouse_no4": form.cleaned_data["spouse_no4"],
                "spouse_email4": form.cleaned_data["spouse_email4"],
                "spouse_passport4": form.cleaned_data["spouse_passport4"],
                "spouse_relation4": form.cleaned_data["spouse_relation4"],
                "spouse_name5": form.cleaned_data["spouse_name5"],
                "spouse_no5": form.cleaned_data["spouse_no5"],
                "spouse_email5": form.cleaned_data["spouse_email5"],
                "spouse_passport5": form.cleaned_data["spouse_passport5"],
                "spouse_relation5": form.cleaned_data["spouse_relation5"],
            }

            for i in range(1, 6):
                spouse_dob = form.cleaned_data.get("spouse_dob")
                spouse_dob = form.cleaned_data.get(f"spouse_dob{i}")

                if spouse_dob:
                    cleaned_data["spouse_dob"] = spouse_dob.strftime("%Y-%m-%d")
                    cleaned_data[f"spouse_dob{i}"] = spouse_dob.strftime("%Y-%m-%d")

            # Merge personal details with receiver details
            merged_data = {**enquiry_form1, **cleaned_data}

            # Save the merged data to the session
            request.session["enquiry_form2"] = merged_data
            return redirect("emp_enquiry_form3")

        return render(
            request,
            "Employee/Enquiry/lead2.html",
            {"form": form},
        )


class emp_Enquiry3View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm3()
        user = request.user
        dep = user.employee.department
        context = {"dep": dep, "form": form}
        return render(request, "Employee/Enquiry/lead3.html", context)

    def post(self, request):
        form1_data = request.session.get("enquiry_form1", {})
        form2_data = request.session.get("enquiry_form2", {})
        form3 = EnquiryForm3(request.POST)

        if form3.is_valid():
            user = request.user
            form3.instance.assign_to_employee = user.employee
            # Merge data from all three forms
            merged_data = {
                **form1_data,
                **form2_data,
                **form3.cleaned_data,
            }

            # Save the merged data to the database
            enquiry = Enquiry(**merged_data)

            enquiry.created_by = self.request.user
            enquiry.lead_status = "New Lead"
            enquiry.save()
            employee_id = self.request.user.employee.id

            create_admin_notification("New Lead Added")

            current_count = Notification.objects.filter(is_seen=False).count()
            send_notification_admin("New Lead Added", current_count)

            messages.success(request, "Enquiry Added successfully")

            # Clear session data after successful submission
            request.session.pop("enquiry_form1", None)
            request.session.pop("enquiry_form2", None)

            return redirect("emp_enquiry_form4", id=enquiry.id)

        return render(
            request,
            "Employee/Enquiry/lead3.html",
            {"form": form3},
        )

    def get_success_url(self):
        enquiry_id = self.object.id
        return reverse_lazy("emp_enquiry_form4", kwargs={"id": enquiry_id})


def get_presale_employee():
    return Employee.objects.filter(department="Presales")


@login_required
def empdocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()
    user = request.user
    dep = user.employee.department

    doc_file = DocumentFiles.objects.filter(enquiry_id=enq)

    case_categories = CaseCategoryDocument.objects.filter(country=enq.Visa_country)

    documents_prefetch = Prefetch(
        "document",
        queryset=Document.objects.select_related("document_category", "lastupdated_by"),
    )

    case_categories = case_categories.prefetch_related(documents_prefetch)

    grouped_documents = {}

    for case_category in case_categories:
        for document in case_category.document.all():
            document_category = document.document_category
            testing = document.document_category.id

            if document_category not in grouped_documents:
                grouped_documents[document_category] = []

            grouped_documents[document_category].append(document)

    context = {
        "enq": enq,
        "grouped_documents": grouped_documents,
        "doc_file": doc_file,
        "dep": dep,
    }

    return render(request, "Employee/Enquiry/lead4.html", context)


@login_required
def emp_upload_document(request):
    if request.method == "POST":
        document_id = request.POST.get("document_id")
        enq_id = request.POST.get("enq_id")
        document = Document.objects.get(pk=document_id)
        document_file = request.FILES.get("document_file")
        enq = Enquiry.objects.get(id=enq_id)
        documest_files = DocumentFiles.objects.create(
            document_file=document_file,
            document_id=document,
            enquiry_id=enq,
            lastupdated_by=request.user,
        )
        documest_files.save()
        return redirect("emp_enquiry_form4", enq_id)


@login_required
def emp_delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("emp_enquiry_form4", enqq)


# -------------------------------------- Leads ------------------------------

# testrrrrrrrrrrrrrrrr


@login_required
def employee_lead_list(request):
    user = request.user

    if user.is_authenticated:
        if user.user_type == "3":
            emp = user.employee
            dep = emp.department
            if dep == "Presales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Sales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_sales_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")

            elif dep == "Documentation":
                enq = Enquiry.objects.filter(
                    Q(assign_to_documentation_employee=user.employee)
                    | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Visa Team":
                enq = Enquiry.objects.filter(
                    Q(assign_to_visa_team_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Assesment":
                enq = Enquiry.objects.filter(
                    Q(assign_to_assesment_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            else:
                enq = Enquiry.objects.filter(created_by=request.user)

            context = {"enq": enq, "user": user, "dep": dep}
    return render(request, "Employee/Enquiry/lead_list.html", context)


@login_required
def employee_lead_grid(request):
    user = request.user

    if user.is_authenticated:
        if user.user_type == "3":
            emp = user.employee
            dep = emp.department
            if dep == "Presales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Sales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_sales_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")

            elif dep == "Documentation":
                enq = Enquiry.objects.filter(
                    Q(assign_to_documentation_employee=user.employee)
                    | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Visa Team":
                enq = Enquiry.objects.filter(
                    Q(assign_to_visa_team_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Assesment":
                enq = Enquiry.objects.filter(
                    Q(assign_to_assesment_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            else:
                enq = Enquiry.objects.filter(created_by=request.user)
            context = {"enq": enq, "user": user, "dep": dep}
    return render(request, "Employee/Enquiry/lead-grid.html", context)


def employee_enrolled_lead(request):
    user = request.user

    if user.is_authenticated:
        if user.user_type == "3":
            emp = user.employee
            dep = emp.department
            if dep == "Presales":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_employee=user.employee,
                ).order_by("-id")
            elif dep == "Sales":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_sales_employee=user.employee,
                ).order_by("-id")
            elif dep == "Documentation":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_documentation_employee=user.employee,
                ).order_by("-id")
            elif dep == "Visa Team":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_visa_team_employee=user.employee,
                ).order_by("-id")
            else:
                enq = None

            context = {"enq": enq, "user": user, "dep": dep}

    return render(
        request, "Employee/Enquiry/Enrolled Enquiry/Enrolledleads.html", context
    )


def employee_enrolled_grid(request):
    user = request.user

    if user.is_authenticated:
        if user.user_type == "3":
            emp = user.employee
            dep = emp.department
            if dep == "Presales":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_employee=user.employee,
                ).order_by("-id")
            elif dep == "Sales":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_sales_employee=user.employee,
                ).order_by("-id")
            elif dep == "Documentation":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_documentation_employee=user.employee,
                ).order_by("-id")
            elif dep == "Visa Team":
                enq = Enquiry.objects.filter(
                    Q(lead_status="Enrolled")
                    | Q(lead_status="Inprocess")
                    | Q(lead_status="Ready To Submit")
                    | Q(lead_status="Appointment")
                    | Q(lead_status="Ready To Collection")
                    | Q(lead_status="Result")
                    | Q(lead_status="Delivery"),
                    assign_to_visa_team_employee=user.employee,
                ).order_by("-id")
            else:
                enq = None

            context = {"enq": enq, "user": user, "dep": dep}
    return render(request, "Employee/Enquiry/enroll_lead-grid.html", context)


# --------------------------------------------------------------


def get_sale_employee():
    return Employee.objects.filter(department="Sales")


def get_assesment_employee():
    return Employee.objects.filter(department="Assesment")


def get_documentation_team_employee():
    return Employee.objects.filter(department="Documentation")


def get_visa_team_employee():
    return Employee.objects.filter(department="Visa Team")


def preenrolled_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    agnt = enquiry.assign_to_agent
    sale_Emp = enquiry.assign_to_sales_employee
    doc_Emp = enquiry.assign_to_documentation_employee
    visa_Emp = enquiry.assign_to_visa_team_employee

    if agnt:
        agent_id = Agent.objects.get(id=agnt.id)
        sales_emp = agent_id.assign_employee

        enquiry.lead_status = "PreEnrolled"
        enquiry.assign_to_sales_employee = sales_emp
        enquiry.save()
        return redirect("employee_lead_list")

    if sale_Emp:
        enquiry.lead_status = "PreEnrolled"
        enquiry.save()
        return redirect("employee_lead_list")

    if doc_Emp:
        enquiry.lead_status = "PreEnrolled"
        enquiry.save()
        return redirect("employee_lead_list")
    if visa_Emp:
        enquiry.lead_status = "PreEnrolled"
        enquiry.save()
        return redirect("employee_lead_list")

    else:
        last_assigned_index = cache.get("last_assigned_index") or 0
        saleteam_employees = get_sale_employee()

        next_index = (last_assigned_index + 1) % saleteam_employees.count()
        enquiry.assign_to_sales_employee = saleteam_employees[next_index]
        enquiry.lead_status = "PreEnrolled"
        enquiry.assign_to_sales_employee

        enquiry.save()
        cache.set("last_assigned_index", next_index)

        create_notification(enquiry.assign_to_sales_employee, "New Lead Assign Added")

        current_count = Notification.objects.filter(
            is_seen=False, employee=enquiry.assign_to_sales_employee
        ).count()

        employee_id = enquiry.assign_to_sales_employee.id
        send_notification(employee_id, "New Lead Assign Added", current_count)

        # return redirect("employee_leads")

    return redirect("employee_lead_list")


def active_save(request, id):
    enquiry = Enquiry.objects.get(id=id)

    assesment_Emp = enquiry.assign_to_assesment_employee

    if assesment_Emp:
        enquiry.lead_status = "Active"
        enquiry.save()

        return redirect("employee_lead_list")
    else:
        last_assigned_index = cache.get("last_assigned_index") or 0
        assesment_team_employees = get_assesment_employee()

        next_index = (last_assigned_index + 1) % assesment_team_employees.count()
        enquiry.assign_to_assesment_employee = assesment_team_employees[next_index]
        enquiry.lead_status = "Active"
        enquiry.assign_to_assesment_employee

        enquiry.save()
        cache.set("last_assigned_index", next_index)
        create_notification(
            enquiry.assign_to_assesment_employee, "New Lead Assign Added"
        )

        current_count = Notification.objects.filter(
            is_seen=False, employee=enquiry.assign_to_assesment_employee
        ).count()

        employee_id = enquiry.assign_to_assesment_employee.id
        send_notification(employee_id, "New Lead Assign Added", current_count)

    return redirect("employee_lead_list")


def enrolled_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    doc_id = enquiry.assign_to_documentation_employee
    if doc_id:
        enquiry.lead_status = "Enrolled"
        enquiry.save()

    last_assigned_index = cache.get("last_assigned_index") or 0
    documentation_team_employees = get_documentation_team_employee()
    if documentation_team_employees.exists():
        next_index = (last_assigned_index + 1) % documentation_team_employees.count()
        enquiry.assign_to_documentation_employee = documentation_team_employees[
            next_index
        ]
        enquiry.lead_status = "Enrolled"
        enquiry.save()
        cache.set("last_assigned_index", next_index)

        create_notification(
            enquiry.assign_to_documentation_employee, "New Lead Assign Added"
        )

        current_count = Notification.objects.filter(
            is_seen=False, employee=enquiry.assign_to_documentation_employee
        ).count()

        employee_id = enquiry.assign_to_documentation_employee.id
        send_notification(employee_id, "New Lead Assign Added", current_count)

    return redirect("employee_lead_list")


def enprocess_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    emp_doc_team = enquiry.assign_to_documentation_employee
    if emp_doc_team:
        enquiry.lead_status = "Inprocess"
        enquiry.save()

    last_assigned_index = cache.get("last_assigned_index") or 0
    # visa_team_employees = get_visa_team_employee()
    visa_team_employees = Employee.objects.filter(
        department="Visa Team", color_code=enquiry.color_code
    )

    if visa_team_employees.exists():
        next_index = (last_assigned_index + 1) % visa_team_employees.count()
        enquiry.assign_to_visa_team_employee = visa_team_employees[next_index]
        enquiry.lead_status = "Inprocess"
        enquiry.save()
        cache.set("last_assigned_index", next_index)

        create_notification(
            enquiry.assign_to_visa_team_employee, "New Lead Assign Added"
        )

        current_count = Notification.objects.filter(
            is_seen=False, employee=enquiry.assign_to_visa_team_employee
        ).count()

        employee_id = enquiry.assign_to_visa_team_employee.id
        send_notification(employee_id, "New Lead Assign Added", current_count)

    return redirect("employee_lead_list")


def reject_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Reject"
    enquiry.save()
    return redirect("employee_lead_list")


def ready_to_submit_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Ready To Submit"
    enquiry.save()
    return redirect("employee_lead_list")


def appointment_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Appointment"
    enquiry.save()
    return redirect("employee_lead_list")


def ready_to_collection_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Ready To Collection"
    enquiry.save()
    return redirect("employee_lead_list")


def result_save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Result"
    enquiry.save()
    return redirect("employee_lead_list")


def delivery_Save(request, id):
    enquiry = Enquiry.objects.get(id=id)
    enquiry.lead_status = "Delivery"
    enquiry.save()
    return redirect("employee_lead_list")


def enq_appointment_Save(request):
    if request.method == "POST":
        enq = request.POST.get("enq_id")
        enq_id = Enquiry.objects.get(id=enq)

        desc = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        try:
            enqapp = EnqAppointment.objects.get(enquiry=enq_id)

            # Existing EnqAppointment found

            enqapp.description = desc
            enqapp.enquiry = enq_id
            enqapp.date = date
            enqapp.time = time
            enqapp.created_by = request.user
            enqapp.save()
        except EnqAppointment.DoesNotExist:
            # No existing EnqAppointment found, create a new one
            appt = EnqAppointment.objects.create(
                enquiry=enq_id,
                description=desc,
                date=date,
                time=time,
                created_by=request.user,
            )
            appt.save()

        return redirect("employee_lead_list")


def appointment_done(request, id):
    enq = Enquiry.objects.get(id=id)

    enq_appointment = EnqAppointment.objects.get(enquiry=enq)
    enq_appointment.status = "Done"

    enq_appointment.save()
    return redirect("employee_lead_list")


def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        data = response.json()
        return data["ip"]
    except Exception as e:
        # Handle the exception (e.g., log the error)
        return None


def emp_add_notes(request):
    if request.method == "POST":
        enq_id = request.POST.get("enq_id")
        notes_text = request.POST.get("notes")
        file = request.FILES.get("file")
        user = request.user

        try:
            enq = Enquiry.objects.get(id=enq_id)
            ip_address = get_public_ip()

            notes = Notes.objects.create(
                enquiry=enq,
                notes=notes_text,
                file=file,
                ip_address=ip_address,
                created_by=user,
            )
            notes.save()

        except Enquiry.DoesNotExist:
            pass

    return redirect("employee_lead_list")


# ------------------------------------------ AGent Details --------------------------


def emp_add_agent(request):
    logged_in_user = request.user
    relevant_employees = Employee.objects.all()
    user = request.user

    dep = user.employee.department

    if request.method == "POST":
        type = request.POST.get("type")

        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = request.POST.get("password")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zipcode = request.POST.get("zipcode")
        files = request.FILES.get("files")

        existing_agent = CustomUser.objects.filter(username=email)
        fullname = str(firstname + " " + lastname)
        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return redirect("emp_add_agent")

            if type == "Outsourcing Partner":
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="5",
                )
                logged_in_user = request.user

                user.outsourcingagent.type = type
                user.outsourcingagent.contact_no = contact
                user.outsourcingagent.country = country
                user.outsourcingagent.state = state
                user.outsourcingagent.City = city
                user.outsourcingagent.Address = address
                user.outsourcingagent.zipcode = zipcode
                user.outsourcingagent.profile_pic = files
                user.outsourcingagent.registerdby = logged_in_user
                user.outsourcingagent.assign_employee = logged_in_user.employee
                chat_group_name = f"{fullname} Group"
                chat_group = ChatGroup.objects.create(
                    group_name=chat_group_name,
                )
                chat_group.group_member.add(user.outsourcingagent.assign_employee.users)
                chat_group.group_member.add(user)

                user.save()

                # create_admin_notification("New Lead Added")
                msg = f"New OutSourceAgent Added({fullname})"
                create_admin_notification(msg)

                current_count = Notification.objects.filter(is_seen=False).count()
                send_notification_admin(msg, current_count)
                # send_notification_admin("New Lead Assign Added", current_count)

                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an Outsource Agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com/Agent/Login/ \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )

                recipient_list = [email]

                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="5"
                )

                mobile_number = contact

                message = (
                    f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                    f" Hello {firstname} {lastname}, \n\n"
                    f" Welcome to Sky Trails! Your OutsourceAgent account is ready to roll. \n\n"
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
                response = send_whatsapp_message(mobile_number, message)

                messages.success(request, "OutSource Agent Added Successfully")
                return redirect("emp_all_outsource_agent")

            else:
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="4",
                )
                logged_in_user = request.user

                user.agent.type = type
                user.agent.contact_no = contact
                user.agent.country = country
                user.agent.state = state
                user.agent.City = city
                user.agent.Address = address
                user.agent.zipcode = zipcode
                user.agent.profile_pic = files
                user.agent.registerdby = logged_in_user
                user.agent.assign_employee = logged_in_user.employee
                chat_group_name = f"{fullname} Group"
                chat_group = ChatGroup.objects.create(
                    group_name=chat_group_name,
                )
                chat_group.group_member.add(user.agent.assign_employee.users)
                chat_group.group_member.add(user)
                user.save()

                msg = f"New Agent Added({fullname})"
                create_admin_notification(msg)

                current_count = Notification.objects.filter(is_seen=False).count()
                send_notification_admin(msg, current_count)

                context = {"employees": relevant_employees, "dep": dep}

                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com/Agent/Login/ \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )

                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="4"
                )

                mobile_number = contact

                message = (
                    f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                    f" Hello {firstname} {lastname}, \n\n"
                    f" Welcome to Sky Trails! Your Agent account is ready to roll. \n\n"
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
                response = send_whatsapp_message(mobile_number, message)

                messages.success(request, "Agent Added Successfully")
                return redirect("emp_agent_list")

        except Exception as e:
            messages.warning(request, e)

    context = {"employees": relevant_employees, "dep": dep}

    return render(request, "Employee/Agent Management/addagent.html", context)


class emp_all_agent(ListView):
    model = Agent
    template_name = "Employee/Agent Management/agentlist.html"
    context_object_name = "agent"

    def get_queryset(self):
        user = self.request.user.employee
        return Agent.objects.filter(
            Q(registerdby=self.request.user) | Q(assign_employee=user)
        ).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["employee_queryset"] = Employee.objects.all()
        context["dep"] = dep
        return context


class emp_allGrid_agent(ListView):
    model = Agent
    template_name = "Employee/Agent Management/agentgrid.html"
    context_object_name = "agent"

    def get_queryset(self):
        user = self.request.user.employee
        return Agent.objects.filter(assign_employee=user).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["employee_queryset"] = Employee.objects.all()
        context["dep"] = dep
        return context


def employee_agent_delete(request, id):
    try:
        agent = Agent.objects.get(id=id)
        custom_user = agent.users
        custom_user.delete()

        agent.delete()

        messages.success(request, "Agent Deleted Successfully ")
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found")

    return HttpResponseRedirect(reverse("emp_agent_list"))


def emp_agent_details(request, id):
    agent = Agent.objects.get(id=id)
    users = agent.users
    user = request.user
    dep = user.employee.department

    if request.method == "POST":
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")

        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        maritial = request.POST.get("maritial")
        original_pic = request.FILES.get("original_pic")
        organization = request.POST.get("organization")
        business_type = request.POST.get("business_type")
        registration = request.POST.get("registration")
        address = request.POST.get("address")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        zipcode = request.POST.get("zipcode")
        accountholder = request.POST.get("accountholder")
        bankname = request.POST.get("bankname")
        branchname = request.POST.get("branchname")
        account = request.POST.get("account")
        ifsc = request.POST.get("ifsc")

        if dob:
            users.agent.dob = dob
        if gender:
            users.agent.gender = gender
        if maritial:
            users.agent.marital_status = maritial
        if original_pic:
            users.agent.profile_pic = original_pic

        users.first_name = firstname

        users.agent.organization_name = organization
        users.agent.business_type = business_type
        users.agent.registration_number = registration
        users.agent.Address = address
        users.agent.country = country
        users.agent.state = state
        users.agent.City = city
        users.agent.zipcode = zipcode
        users.agent.account_holder = accountholder
        users.agent.bank_name = bankname
        users.agent.branch_name = branchname
        users.agent.account_no = account
        users.agent.ifsc_code = ifsc

        users.save()
        messages.success(request, "Updated Successfully")
        return redirect("emp_agent_details", id)

    context = {"agent": agent, "dep": dep}
    return render(request, "Employee/Agent Management/Update/agentupdate.html", context)


def employee_agent_agreement(request, id):
    agent = Agent.objects.get(id=id)
    user = request.user
    dep = user.employee.department
    agntagreement = AgentAgreement.objects.filter(agent=agent)
    if request.method == "POST":
        name = request.POST.get("agreement_name")
        file = request.FILES.get("file")
        agreement = AgentAgreement.objects.create(
            agent=agent, agreement_name=name, agreement_file=file
        )
        agreement.save()
        messages.success(request, "Agreement Updated Succesfully...")
        return redirect("employee_agent_agreement", id)
    context = {"agent": agent, "agreement": agntagreement, "dep": dep}
    return render(
        request, "Employee/Agent Management/Update/agentagreement.html", context
    )


def employee_agent_agreement_update(request, id):
    agree = AgentAgreement.objects.get(id=id)
    agent = agree.agent

    if request.method == "POST":
        agntagreement = AgentAgreement.objects.get(id=id)
        agreement_name = request.POST.get("agreement_name")
        file = request.FILES.get("file")

        agntagreement.agreement_name = agreement_name
        if file:
            agntagreement.agreement_file = file
        agntagreement.save()
        messages.success(request, "Agreement Updated Successfully...")
        return redirect("employee_agent_agreement", agent.id)


def emp_agent_agreement_delete(request, id):
    agree = AgentAgreement.objects.get(id=id)
    agent = agree.agent
    agreement = AgentAgreement.objects.get(id=id)
    agreement.delete()
    messages.success(request, "Agreement Deleted Successfully...")
    return redirect("employee_agent_agreement", agent.id)


def emp_agent_kyc(request, id):
    agent = Agent.objects.get(id=id)
    kyc_agent = AgentKyc.objects.filter(agent=agent).first
    user = request.user
    dep = user.employee.department
    # kyc_agent = get_object_or_404(AgentKyc, agent=agent)
    kyc_id = None

    if request.method == "POST":
        adharfront_file = request.FILES.get("adharfront_file")
        adharback_file = request.FILES.get("adharback_file")
        pan_file = request.FILES.get("pan_file")
        registration_file = request.FILES.get("registration_file")
        try:
            kyc_id = AgentKyc.objects.get(agent=agent)

            if kyc_id:
                if adharfront_file:
                    kyc_id.adhar_card_front = adharfront_file
                if adharback_file:
                    kyc_id.adhar_card_back = adharback_file
                if pan_file:
                    kyc_id.pancard = pan_file
                if registration_file:
                    kyc_id.registration_certificate = registration_file
                kyc_id.save()
                messages.success(request, "Kyc Added Successfully..")
                return redirect("admin_agent_kyc", id)
            else:
                pass

        except AgentKyc.DoesNotExist:
            kyc_id = None
            kyc = AgentKyc.objects.create(
                agent=agent,
                adhar_card_front=adharfront_file,
                adhar_card_back=adharback_file,
                pancard=pan_file,
                registration_certificate=registration_file,
            )
            kyc.save()
            messages.success(request, "Kyc Added Successfully..")
            return redirect("emp_agent_kyc", id)

    context = {"agent": agent, "kyc_id": kyc_id, "kyc_agent": kyc_agent, "dep": dep}

    return render(request, "Employee/Agent Management/Update/agentkyc.html", context)


# ------------------------------ Outsource Agent --------------------------
class emp_all_outsource_agent(ListView):
    model = OutSourcingAgent
    template_name = "Employee/Agent Management/outsourcelist.html"
    context_object_name = "agentoutsource"

    def get_queryset(self):
        user = self.request.user.employee
        return OutSourcingAgent.objects.filter(assign_employee=user).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep
        context["employee_queryset"] = Employee.objects.all()

        return context


class emp_allGrid_outsource_agent(ListView):
    model = OutSourcingAgent
    template_name = "Employee/Agent Management/outsorcegrid.html"
    context_object_name = "agentoutsource"

    def get_queryset(self):
        user = self.request.user.employee
        return OutSourcingAgent.objects.filter(assign_employee=user).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep
        context["employee_queryset"] = Employee.objects.all()

        return context


def emp_outsourceagent_details(request, id):
    outsourceagent = OutSourcingAgent.objects.get(id=id)
    users = users = outsourceagent.users
    user = request.user
    dep = user.employee.department

    if request.method == "POST":
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")

        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        maritial = request.POST.get("maritial")
        original_pic = request.FILES.get("original_pic")
        organization = request.POST.get("organization")
        business_type = request.POST.get("business_type")
        registration = request.POST.get("registration")
        address = request.POST.get("address")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        zipcode = request.POST.get("zipcode")
        accountholder = request.POST.get("accountholder")
        bankname = request.POST.get("bankname")
        branchname = request.POST.get("branchname")
        account = request.POST.get("account")
        ifsc = request.POST.get("ifsc")

        if dob:
            users.outsourcingagent.dob = dob
        if gender:
            users.outsourcingagent.gender = gender
        if maritial:
            users.outsourcingagent.marital_status = maritial
        if original_pic:
            users.outsourcingagent.profile_pic = original_pic

        users.first_name = firstname

        users.outsourcingagent.organization_name = organization
        users.outsourcingagent.business_type = business_type
        users.outsourcingagent.registration_number = registration
        users.outsourcingagent.Address = address
        users.outsourcingagent.country = country
        users.outsourcingagent.state = state
        users.outsourcingagent.City = city
        users.outsourcingagent.zipcode = zipcode
        users.outsourcingagent.account_holder = accountholder
        users.outsourcingagent.bank_name = bankname
        users.outsourcingagent.branch_name = branchname
        users.outsourcingagent.account_no = account
        users.outsourcingagent.ifsc_code = ifsc

        users.save()
        messages.success(request, "Updated Successfully")
        return redirect("emp_outsourceagent_details", id)

    context = {"agent": outsourceagent, "dep": dep}
    return render(
        request,
        "Employee/Agent Management/OutsourceUpdate/outsource_agentupdate.html",
        context,
    )


def emp_outsource_agent_agreement(request, id):
    outsourceagent = OutSourcingAgent.objects.get(id=id)
    user = request.user
    dep = user.employee.department

    agntagreement = AgentAgreement.objects.filter(outsourceagent=outsourceagent)
    if request.method == "POST":
        name = request.POST.get("agreement_name")
        file = request.FILES.get("file")
        agreement = AgentAgreement.objects.create(
            outsourceagent=outsourceagent, agreement_name=name, agreement_file=file
        )
        agreement.save()
        messages.success(request, "Agreement Updated Succesfully...")
        return redirect("emp_outsource_agent_agreement", id)
    # context = {"agent": agent, "agreement": agntagreement}
    context = {"agent": outsourceagent, "agreement": agntagreement, "dep": dep}
    return render(
        request,
        "Employee/Agent Management/OutsourceUpdate/outsource_agentagreement.html",
        context,
    )


def emp_outsourceagent_agreement_update(request, id):
    if request.method == "POST":
        agntagreement = AgentAgreement.objects.get(id=id)
        outsource = agntagreement.outsourceagent
        agreement_name = request.POST.get("agreement_name")
        file = request.FILES.get("file")

        agntagreement.agreement_name = agreement_name
        if file:
            agntagreement.agreement_file = file
        agntagreement.save()
        messages.success(request, "Agreement Updated Successfully...")
        return redirect("emp_outsource_agent_agreement", outsource.id)


def emp_outsource_agent_agreement_delete(request, id):
    agree = AgentAgreement.objects.get(id=id)
    agent = agree.outsourceagent
    agreement = AgentAgreement.objects.get(id=id)
    agreement.delete()
    messages.success(request, "Agreement Deleted Successfully...")
    return redirect("emp_outsource_agent_agreement", agent.id)


def emp_outstsourceagent_delete(request, id):
    try:
        outsourceagent = OutSourcingAgent.objects.get(id=id)

        custom_user = outsourceagent.users
        custom_user.delete()

        outsourceagent.delete()

        messages.success(request, "OutSourceAgent Deleted Successfully")
    except OutSourcingAgent.DoesNotExist:
        messages.error(request, "OutSourceAgent not found")

    return HttpResponseRedirect(reverse("emp_all_outsource_agent"))


def emp_outsource_agent_kyc(request, id):
    agent = OutSourcingAgent.objects.get(id=id)

    kyc_agent = AgentKyc.objects.filter(outsourceagent=agent).first
    user = request.user
    dep = user.employee.department
    # kyc_agent = get_object_or_404(AgentKyc, agent=agent)
    kyc_id = None

    if request.method == "POST":
        adharfront_file = request.FILES.get("adharfront_file")
        adharback_file = request.FILES.get("adharback_file")
        pan_file = request.FILES.get("pan_file")
        registration_file = request.FILES.get("registration_file")
        try:
            kyc_id = AgentKyc.objects.get(outsourceagent=agent)

            if kyc_id:
                if adharfront_file:
                    kyc_id.adhar_card_front = adharfront_file
                if adharback_file:
                    kyc_id.adhar_card_back = adharback_file
                if pan_file:
                    kyc_id.pancard = pan_file
                if registration_file:
                    kyc_id.registration_certificate = registration_file
                kyc_id.save()
                messages.success(request, "Kyc Added Successfully..")
                return redirect("emp_outsource_agent_kyc", id)
            else:
                print("workingggggggg")

        except AgentKyc.DoesNotExist:
            kyc_id = None
            kyc = AgentKyc.objects.create(
                outsourceagent=agent,
                adhar_card_front=adharfront_file,
                adhar_card_back=adharback_file,
                pancard=pan_file,
                registration_certificate=registration_file,
            )
            kyc.save()
            messages.success(request, "Kyc Added Successfully..")
            return redirect("emp_outsource_agent_kyc", id)

    context = {"agent": agent, "kyc_id": kyc_id, "kyc_agent": kyc_agent, "dep": dep}

    return render(
        request,
        "Employee/Agent Management/OutsourceUpdate/outsource_agentkyc.html",
        context,
    )


# --------------------------------------- Enrolled ------------------------------
def emp_edit_enrolled_application(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    user = request.user
    dep = user.employee.department
    form = FollowUpForm()

    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "dep": dep,
        "form": form,
    }

    if request.method == "POST":
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        dob = request.POST.get("dob")
        try:
            dob_obj = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            dob_obj = None

        gender = request.POST.get("gender")
        maritialstatus = request.POST.get("maritialstatus")
        digitalsignature = request.FILES.get("digitalsignature")
        spouse_name = request.POST.get("spouse_name")
        spouse_no = request.POST.get("spouse_no")
        spouse_email = request.POST.get("spouse_email")
        spouse_passport = request.POST.get("spouse_passport")
        spouse_dob = request.POST.get("spouse_dob")
        spouse_relation = request.POST.get("spouse_relation")

        spouse_name1 = request.POST.get("spouse_name1")
        spouse_no1 = request.POST.get("spouse_no1")
        spouse_email1 = request.POST.get("spouse_email1")
        spouse_passport1 = request.POST.get("spouse_passport1")
        spouse_dob1 = request.POST.get("spouse_dob1")
        spouse_relation1 = request.POST.get("spouse_relation1")

        spouse_name2 = request.POST.get("spouse_name2")
        spouse_no2 = request.POST.get("spouse_no2")
        spouse_email2 = request.POST.get("spouse_email2")
        spouse_passport2 = request.POST.get("spouse_passport2")
        spouse_dob2 = request.POST.get("spouse_dob2")
        spouse_relation2 = request.POST.get("spouse_relation2")

        spouse_name3 = request.POST.get("spouse_name3")
        spouse_no3 = request.POST.get("spouse_no3")
        spouse_email3 = request.POST.get("spouse_email3")
        spouse_passport3 = request.POST.get("spouse_passport3")
        spouse_dob3 = request.POST.get("spouse_dob3")
        spouse_relation3 = request.POST.get("spouse_relation3")

        spouse_name4 = request.POST.get("spouse_name4")
        spouse_no4 = request.POST.get("spouse_no4")
        spouse_email4 = request.POST.get("spouse_email4")
        spouse_passport4 = request.POST.get("spouse_passport4")
        spouse_dob4 = request.POST.get("spouse_dob4")
        spouse_relation4 = request.POST.get("spouse_relation4")

        spouse_name5 = request.POST.get("spouse_name5")
        spouse_no5 = request.POST.get("spouse_no5")
        spouse_email5 = request.POST.get("spouse_email5")
        spouse_passport5 = request.POST.get("spouse_passport5")
        spouse_dob5 = request.POST.get("spouse_dob5")
        spouse_relation5 = request.POST.get("spouse_relation5")

        try:
            spouse_dob_obj = datetime.strptime(spouse_dob, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj = None

        try:
            spouse_dob_obj1 = datetime.strptime(spouse_dob1, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj1 = None

        try:
            spouse_dob_obj2 = datetime.strptime(spouse_dob2, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj2 = None

        try:
            spouse_dob_obj3 = datetime.strptime(spouse_dob3, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj3 = None

        try:
            spouse_dob_obj4 = datetime.strptime(spouse_dob4, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj4 = None

        try:
            spouse_dob_obj5 = datetime.strptime(spouse_dob5, "%Y-%m-%d").date()
        except ValueError:
            spouse_dob_obj5 = None

        email = request.POST.get("email")
        contact = request.POST.get("contact")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        Country = request.POST.get("Country")

        emergencyname = request.POST.get("emergencyname")
        emergencyphone = request.POST.get("emergencyphone")
        emergencyemail = request.POST.get("emergencyemail")
        applicantrelation = request.POST.get("applicantrelation")

        passportnumber = request.POST.get("passportnumber")
        issuedate = request.POST.get("issuedate")
        try:
            issuedate_obj = datetime.strptime(issuedate, "%Y-%m-%d").date()
        except ValueError:
            issuedate_obj = None

        expirydate = request.POST.get("expirydate")
        try:
            expirydate_obj = datetime.strptime(expirydate, "%Y-%m-%d").date()
        except ValueError:
            expirydate_obj = None

        issue_country = request.POST.get("issuecountry")
        birthcity = request.POST.get("birthcity")
        country_of_birth = request.POST.get("country_of_birth")

        nationality = request.POST.get("nationality")
        citizenship = request.POST.get("citizenships")
        more_than_one_country = request.POST.get("more_than_one_country")
        studyin_in_other_country = request.POST.get("studyin_in_other_country")

        citizenstatus = request.POST.get("citizenstatus")
        studystatus = request.POST.get("studystatus")

        citizen = request.POST.get("citizen")

        enquiry.FirstName = firstname
        enquiry.LastName = lastname
        enquiry.Dob = dob_obj
        enquiry.Gender = gender
        enquiry.marital_status = maritialstatus
        if digitalsignature:
            enquiry.digital_signature = digitalsignature
        enquiry.spouse_name = spouse_name
        enquiry.spouse_no = spouse_no
        enquiry.spouse_email = spouse_email
        enquiry.spouse_passport = spouse_passport
        enquiry.spouse_dob = spouse_dob_obj
        enquiry.spouse_relation = spouse_relation
        enquiry.spouse_name1 = spouse_name1
        enquiry.spouse_no1 = spouse_no1
        enquiry.spouse_email1 = spouse_email1
        enquiry.spouse_passport1 = spouse_passport1
        enquiry.spouse_dob1 = spouse_dob_obj1
        enquiry.spouse_relation1 = spouse_relation1

        enquiry.spouse_name2 = spouse_name2
        enquiry.spouse_no2 = spouse_no2
        enquiry.spouse_email2 = spouse_email2
        enquiry.spouse_passport2 = spouse_passport2
        enquiry.spouse_dob2 = spouse_dob_obj2
        enquiry.spouse_relation2 = spouse_relation2

        enquiry.spouse_name3 = spouse_name3
        enquiry.spouse_no3 = spouse_no3
        enquiry.spouse_email3 = spouse_email3
        enquiry.spouse_passport3 = spouse_passport3
        enquiry.spouse_dob3 = spouse_dob_obj3
        enquiry.spouse_relation3 = spouse_relation3

        enquiry.spouse_name4 = spouse_name4
        enquiry.spouse_no4 = spouse_no4
        enquiry.spouse_email4 = spouse_email4
        enquiry.spouse_passport4 = spouse_passport4
        enquiry.spouse_dob4 = spouse_dob_obj4
        enquiry.spouse_relation4 = spouse_relation4

        enquiry.spouse_name5 = spouse_name5
        enquiry.spouse_no5 = spouse_no5
        enquiry.spouse_email5 = spouse_email5
        enquiry.spouse_passport5 = spouse_passport5
        enquiry.spouse_dob5 = spouse_dob_obj5
        enquiry.spouse_relation5 = spouse_relation5
        enquiry.email = email
        enquiry.contact = contact
        enquiry.Country = Country
        enquiry.state = state
        enquiry.city = city
        enquiry.address = address

        enquiry.passport_no = passportnumber
        enquiry.issue_date = issuedate_obj
        enquiry.expirty_Date = expirydate_obj
        enquiry.issue_country = issue_country
        enquiry.city_of_birth = birthcity
        enquiry.country_of_birth = country_of_birth
        enquiry.nationality = nationality
        enquiry.citizenship = citizenship
        enquiry.more_than_one_country = more_than_one_country
        enquiry.studyin_in_other_country = studyin_in_other_country
        enquiry.emergency_name = emergencyname
        enquiry.emergency_phone = emergencyphone
        if emergencyemail != "None":
            enquiry.emergency_email = emergencyemail
        enquiry.relation_With_applicant = applicantrelation
        enquiry.save()
        messages.success(request, "Persoanal Details Updated Successfully....")

        return redirect("emp_edit_enrolled_application", id)

    return render(
        request,
        "Employee/Enquiry/Enrolled Enquiry/Editenrolledpart1.html",
        context,
    )


def emp_combined_view(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    edu_sum = Education_Summary.objects.filter(enquiry_id=enquiry).first
    work_exp = Work_Experience.objects.filter(enquiry_id=enquiry).first
    bk_info = Background_Information.objects.filter(enquiry_id=enquiry).first
    user = request.user
    dep = user.employee.department

    if request.method == "POST":
        # Education Summary
        education_summary, created = Education_Summary.objects.get_or_create(
            enquiry_id=enquiry
        )
        education_summary.highest_level_education = request.POST.get(
            "highest_education"
        )
        education_summary.grading_scheme = request.POST.get("gradingscheme")
        education_summary.grade_avg = request.POST.get("gradeaverage")
        education_summary.recent_college = request.POST.get("recent_college")
        education_summary.country_of_education = request.POST.get("educationcountry")
        education_summary.country_of_institution = request.POST.get("institutecountry")
        education_summary.name_of_institution = request.POST.get("institutename")
        education_summary.primary_language = request.POST.get("instructionlanguage")
        education_summary.institution_from = request.POST.get("institutionfrom")
        try:
            education_summary.institution_from_obj = datetime.strptime(
                education_summary.institution_from, "%Y-%m-%d"
            ).date()
        except ValueError:
            education_summary.institution_from = None
        education_summary.institution_to = request.POST.get("institutionto")
        try:
            education_summary.institution_to_obj = datetime.strptime(
                education_summary.institution_to, "%Y-%m-%d"
            ).date()
        except ValueError:
            education_summary.institution_to = None
        education_summary.degree_Awarded = request.POST.get("degreeawarded")
        education_summary.degree_Awarded_On = request.POST.get("degreeawardedon")
        education_summary.save()

        # Test Score
        examtype = request.POST.get("examtype")
        exam_date = request.POST.get("examdate")

        try:
            exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
        except ValueError:
            exam_date = None
        reading = request.POST.get("reading")
        listening = request.POST.get("listening")
        speaking = request.POST.get("speaking")
        writing = request.POST.get("writing")
        overall_score = request.POST.get("overallscore")

        existing_test_score = TestScore.objects.filter(
            exam_type=examtype, enquiry_id=enquiry
        ).first()
        if reading or exam_date or listening or speaking or writing or overall_score:
            if existing_test_score is None:
                test_scores = TestScore.objects.create(
                    enquiry_id=enquiry,
                    exam_type=examtype,
                    exam_date=exam_date,
                    reading=reading,
                    listening=listening,
                    speaking=speaking,
                    writing=writing,
                    overall_score=overall_score,
                )

            else:
                existing_test_score.exam_date = exam_date
                existing_test_score.reading = reading
                existing_test_score.listening = listening
                existing_test_score.speaking = speaking
                existing_test_score.writing = writing
                existing_test_score.overall_score = overall_score
                existing_test_score.save()

        # Handle Background Information
        background_info, created = Background_Information.objects.get_or_create(
            enquiry_id=enquiry
        )
        background_info.background_information = request.POST.get("australliabefore")
        background_info.save()

        # Handle Work Experience
        work_exp, created = Work_Experience.objects.get_or_create(enquiry_id=enquiry)
        work_exp.company_name = request.POST.get("companyname")
        work_exp.designation = request.POST.get("designation")
        work_exp.from_date = request.POST.get("fromdate")
        try:
            work_exp.from_date_obj = datetime.strptime(
                work_exp.from_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            work_exp.from_date = None
        work_exp.to_date = request.POST.get("todate")
        try:
            work_exp.to_date_obj = datetime.strptime(
                work_exp.to_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            work_exp.to_date = None
        work_exp.address = request.POST.get("address")
        work_exp.city = request.POST.get("city")
        work_exp.state = request.POST.get("state")
        work_exp.describe = request.POST.get("workdetails")
        work_exp.save()

        return redirect("emp_education_summary", id)

    test_scores = TestScore.objects.filter(enquiry_id=enquiry)

    context = {
        "enquiry": enquiry,
        "test_scores": test_scores,
        "education_summary": edu_sum,
        "work_exp": work_exp,
        "bk_info": bk_info,
        "dep": dep,
    }

    return render(
        request, "Employee/Enquiry/Enrolled Enquiry/Editenrolledpart2.html", context
    )


def emp_editproduct_details(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    product = Package.objects.all()
    user = request.user
    dep = user.employee.department
    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "product": product,
        "dep": dep,
    }

    if request.method == "POST":
        source = request.POST.get("source")
        reference = request.POST.get("reference")
        visatype = request.POST.get("visatype")
        visacountry_id = request.POST.get("visacountry_id")
        visacategory_id = request.POST.get("visacategory_id")
        visasubcategory_id = request.POST.get("visasubcategory")
        product_id = request.POST.get("Package")

        visa_country = VisaCountry.objects.get(id=visacountry_id)
        visa_category = VisaCategory.objects.get(id=visacategory_id)
        visa_subcategory = VisaCategory.objects.get(id=visacategory_id)
        package = Package.objects.get(id=product_id)

        enquiry.Source = source
        enquiry.Reference = reference
        enquiry.Visa_type = visatype
        enquiry.Visa_country = visa_country
        enquiry.Visa_category = visa_category
        enquiry.Visa_subcategory = visa_subcategory
        enquiry.Package = package

        enquiry.save()

        return redirect("emp_editproduct_details", id=id)

    return render(
        request,
        "Employee/Enquiry/Enrolled Enquiry/Editenrolledpart3.html",
        context,
    )


def emp_enrolleddocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()
    user = request.user
    dep = user.employee.department

    doc_file = DocumentFiles.objects.filter(enquiry_id=enq)

    case_categories = CaseCategoryDocument.objects.filter(country=enq.Visa_country)

    documents_prefetch = Prefetch(
        "document",
        queryset=Document.objects.select_related("document_category", "lastupdated_by"),
    )

    case_categories = case_categories.prefetch_related(documents_prefetch)

    grouped_documents = {}

    for case_category in case_categories:
        for document in case_category.document.all():
            document_category = document.document_category
            testing = document.document_category.id

            if document_category not in grouped_documents:
                grouped_documents[document_category] = []

            grouped_documents[document_category].append(document)

    context = {
        "enq": enq,
        "grouped_documents": grouped_documents,
        "doc_file": doc_file,
        "dep": dep,
    }

    return render(
        request, "Employee/Enquiry/Enrolled Enquiry/Editenrolledpart4.html", context
    )


def emp_enrolled_upload_document(request):
    if request.method == "POST":
        document_id = request.POST.get("document_id")
        enq_id = request.POST.get("enq_id")
        document = Document.objects.get(pk=document_id)
        document_file = request.FILES.get("document_file")
        enq = Enquiry.objects.get(id=enq_id)
        documest_files = DocumentFiles.objects.create(
            document_file=document_file,
            document_id=document,
            enquiry_id=enq,
            lastupdated_by=request.user,
        )
        documest_files.save()
        return redirect("emp_enrolleddocument", id=enq_id)


def emp_enrolled_delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("emp_enrolleddocument", enqq)


# ------------------------- Followup ---------------------------


def followup(request):
    if request.method == "POST":
        enq = request.POST.get("enq_id")
        enquiry = Enquiry.objects.get(id=enq)

        follow_up_form = FollowUpForm(request.POST)
        if follow_up_form.is_valid():
            follow_up = follow_up_form.save(commit=False)
            follow_up.enquiry = enquiry
            follow_up.created_by = request.user
            follow_up.save()
            messages.success(request, "Followup Created Successfully")
            return redirect("emp_edit_enrolled_application", enquiry.id)


def emp_followup_list(request):
    user = request.user.employee
    user2 = request.user
    form = FollowUpForm()
    priority = PRIORITY_CHOICES
    status = FOLLOWUP_STATUS_CHOICES

    enq_list = Enquiry.objects.filter(
        # Q(created_by=user)
        Q(assign_to_employee=user)
        | Q(assign_to_sales_employee=user)
        | Q(assign_to_documentation_employee=user)
        | Q(assign_to_visa_team_employee=user)
    ).distinct()
    followup = FollowUp.objects.filter(enquiry__in=enq_list)

    context = {
        "followup": followup,
        "form": form,
        "priority": priority,
        "status": status,
    }
    return render(request, "Employee/FollowUp/followup_list.html", context)


def followup_update(request):
    if request.method == "POST":
        followup_id = request.POST.get("followup_id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        follow_up_status = request.POST.get("follow_up_status")
        priority = request.POST.get("priority")
        remark = request.POST.get("remark")

        followup = FollowUp.objects.get(id=followup_id)

        followup.title = title
        followup.description = description
        followup.follow_up_status = follow_up_status
        followup.priority = priority
        followup.calendar = date
        followup.time = time
        followup.remark = remark
        followup.save()
        messages.success(request, "Followup Updated Successfully...")

        return redirect("emp_followup_list")


def emp_followup_delete(request, id):
    followup = FollowUp.objects.get(id=id)
    followup.delete()
    messages.success(request, "Followup Deleted... !!")
    return redirect(emp_followup_list)


###################################### LOGOUT #######################################################


@login_required
def employee_logout(request):
    user = request.user
    user.is_logged_in = False
    user.save()
    logout(request)
    return redirect("/")


############################################### CHANGE PASSWORD ###########################################


@login_required
def ChangePassword(request):
    user = request.user
    admin = Employee.objects.get(users=user)

    if request.method == "POST":
        old_psw = request.POST.get("old_password")
        newpassword = request.POST.get("newpassword")
        confirmpassword = request.POST.get("confirmpassword")

        if check_password(old_psw, admin.users.password):
            if newpassword == confirmpassword:
                admin.users.set_password(newpassword)
                admin.users.save()
                messages.success(
                    request, "Password changed successfully Please Login Again !!"
                )
                return HttpResponseRedirect(reverse("login"))
            else:
                messages.success(request, "New passwords do not match")
                return HttpResponseRedirect(reverse("login"))

        else:
            messages.warning(request, "Old password is not correct")
            return HttpResponseRedirect(reverse("login"))

    return render(request, "Employee/Dashboard/dashboard.html")


# ----------------------------------------- FAQ ------------------------

# ----------------------------------------- FAQ ------------------------


class emp_FAQCreateView(LoginRequiredMixin, CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = "Employee/Queries/add_query.html"
    success_url = reverse_lazy("Emp_pending_queries")

    def form_valid(self, form):
        form.instance.user = self.request.user

        messages.success(self.request, "FAQ Added Successfully.")

        return super().form_valid(form)


def get_pending_queries_count():
    return FAQ.objects.filter(answer__exact="").exclude(answer__isnull=True).count()


class ResolvedFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Employee/Queries/Queries.html"
    context_object_name = "resolved_queries"

    def get_queryset(self):
        return FAQ.objects.all().exclude(answer="")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_queries_count"] = get_pending_queries_count()
        return context


class PendingFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Employee/Queries/PendingQueries.html"
    context_object_name = "pending_queries"

    def get_queryset(self):
        return FAQ.objects.filter(answer__exact="").exclude(answer__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_queries_count"] = self.get_queryset().count()
        return context


def FAQUpdateView(request):
    user = request.user
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        question = request.POST.get("question")
        answer = request.POST.get("answer")

        question_id = FAQ.objects.get(id=question_id)
        question_id.question = question
        question_id.answer = answer

        question_id.user = user

        question_id.save()
        messages.success(request, "Question Updated successfully")
        return HttpResponseRedirect(reverse("Emp_resolved_queries"))


################################################## PRODUCT ################################################


class PackageListView(LoginRequiredMixin, ListView):
    model = Package
    template_name = "Employee/Product/product.html"
    context_object_name = "Package"

    def get_queryset(self):
        return Package.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


class PackageDetailView(LoginRequiredMixin, DetailView):
    model = Package
    template_name = "Employee/Product/Productdetails.html"
    context_object_name = "package"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


class profileview(TemplateView, LoginRequiredMixin):
    template_name = "Employee/Profile/Profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = Enquiry.objects.filter(created_by=self.request.user)
        # employee = Employee.objects.all()
        agent = Agent.objects.filter(assign_employee=self.request.user.employee).count()
        # agent = Agent.objects.get(assign_employee__user=self.request.user)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        context["first_name"] = user.first_name
        context["last_name"] = user.last_name
        context["email"] = user.email
        context["contact"] = user.employee.contact_no

        context["department"] = user.employee.department
        if hasattr(user, "get_user_type_display"):
            context["user_type"] = user.get_user_type_display()
        context["leads"] = leads
        context["agent"] = agent
        context["emp_code"] = user.employee.emp_code

        return context


@login_required
def edit_profile(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        contact = request.POST.get("contact")

        employee_instance = Employee.objects.get(users=request.user)

        employee_instance.users.first_name = first_name
        employee_instance.users.last_name = last_name
        employee_instance.contact_no = contact

        employee_instance.users.save()
        employee_instance.save()

        return redirect("Employee_profile")

    return render(request, "Employee/Profile/Profile.html")


# ---------------------------------------------------

######################################### COUNTRY #################################################


@login_required
def add_visacountry(request):
    visacountry = VisaCountry.objects.all().order_by("-id")
    form = VisaCountryForm(request.POST or None)
    user = request.user
    dep = user.employee.department

    if form.is_valid():
        country_name = form.cleaned_data["country"]
        user = request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        if VisaCountry.objects.filter(country__iexact=country_name).exists():
            messages.error(request, "This country already exists.")
        else:
            form.save()
            messages.success(request, "Visa Country added successfully")
            return HttpResponseRedirect(reverse("emp_add_visacountry"))

    context = {"form": form, "visacountry": visacountry, "dep": dep}
    return render(
        request, "Employee/mastermodule/VisaCountry/VisaCountry.html", context
    )


@login_required
def visacountryupdate_view(request):
    user = request.user
    if request.method == "POST":
        visa_country = request.POST.get("visa_country_id")
        visa_country_name = request.POST.get("visa_country_name")

        visa_Country_id = VisaCountry.objects.get(id=visa_country)
        visa_Country_id.country = visa_country_name.capitalize()

        visa_Country_id.lastupdated_by = f"{user.first_name} {user.last_name}"

        visa_Country_id.save()
        messages.success(request, "Visa Country Updated successfully")
        return HttpResponseRedirect(reverse("emp_add_visacountry"))


@login_required
def import_country(request):
    if request.method == "POST":
        file = request.FILES["file"]
        path = str(file)

        try:
            df = pd.read_excel(file)

            for index, row in df.iterrows():
                country_name = row["countryname"].capitalize()

                visa_country, created = VisaCountry.objects.get_or_create(
                    country=country_name
                )

                if created:
                    visa_country.save()

            messages.success(request, "Data Imported Successfully!!")

        except Exception as e:
            messages.warning(request, e)
            return redirect("emp_add_visacountry")
    return redirect("emp_add_visacountry")


@login_required
def delete_visa_country(request, id):
    visacountry_id = VisaCountry.objects.get(id=id)
    visacountry_id.delete()
    messages.success(request, f"{visacountry_id.country} deleted successfully..")
    return HttpResponseRedirect(reverse("emp_add_visacountry"))


######################################### CATEGORY #################################################


@login_required
def add_visacategory(request):
    visacategory = VisaCategory.objects.all().order_by("-id")
    country = VisaCountry.objects.all()
    user = request.user
    dep = user.employee.department
    form = VisaCategoryForm(request.POST or None)

    if request.method == "POST":
        user = request.user
        form = VisaCategoryForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            subcategory = form.cleaned_data["subcategory"]
            visa_country_id = form.cleaned_data["visa_country_id"]
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"

            if VisaCategory.objects.filter(
                Q(
                    category__iexact=category,
                    subcategory__iexact=subcategory,
                    visa_country_id=visa_country_id,
                )
                | Q(
                    category__iexact=category,
                    subcategory__iexact=subcategory,
                    visa_country_id__isnull=True,
                )
            ).exists():
                messages.error(
                    request,
                    "Category/Subcategory already exists for the selected country.",
                )
            else:
                form.save()
                messages.success(
                    request, "Visa Category/SubCategory Added Successfully"
                )
                return HttpResponseRedirect(reverse("emp_add_visacategory"))

    context = {
        "form": form,
        "visacategory": visacategory,
        "country": country,
        "dep": dep,
    }
    return render(
        request, "Employee/mastermodule/VisaCategory/VisaCategory.html", context
    )


@login_required
def visacategoryupdate_view(request):
    user = request.user
    if request.method == "POST":
        visa_country_id = request.POST.get("visa_contry_id")
        visa_category_name = request.POST.get("visa_category")
        visa_subcategory = request.POST.get("visa_subcategory_id")
        visa_category_id = request.POST.get("visa_category_id")

        visa_country = VisaCountry.objects.get(id=visa_country_id)
        visa_category = VisaCategory.objects.get(id=visa_category_id)

        visa_category.visa_country_id = visa_country
        visa_category.category = visa_category_name
        visa_category.subcategory = visa_subcategory

        visa_category.lastupdated_by = f"{user.first_name} {user.last_name}"

        visa_category.save()
        messages.success(request, "Visa Category Updated successfully")
        return HttpResponseRedirect(reverse("emp_add_visacategory"))


@login_required
def delete_category(request, id):
    category = get_object_or_404(VisaCategory, id=id)
    category.delete()
    messages.success(request, f"{category.category} deleted successfully..")
    return redirect("emp_add_visacategory")


######################################### DOCUMENT CATEGORY ############################################


@login_required
def add_documentcategory(request):
    documentcategory = DocumentCategory.objects.all().order_by("-id")
    user = request.user
    dep = user.employee.department
    form = DocumentCategoryForm(request.POST or None)

    if form.is_valid():
        Document_category = form.cleaned_data["Document_category"]
        user = request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        if DocumentCategory.objects.filter(
            Document_category__iexact=Document_category
        ).exists():
            messages.error(request, "This Document Category already exists.")
        else:
            form.save()
            messages.success(request, "Document Category added successfully")
            return HttpResponseRedirect(reverse("emp_add_documentcategory"))

    context = {"form": form, "documentcategory": documentcategory, "dep": dep}
    return render(
        request, "Employee/mastermodule/DocumentCategory/DocumentCategory.html", context
    )


@login_required
def documentcategoryupdate_view(request):
    user = request.user
    if request.method == "POST":
        document_category = request.POST.get("document_category_id")
        document_category_name = request.POST.get("document_category_name")

        document_category_id = DocumentCategory.objects.get(id=document_category)
        document_category_id.Document_category = document_category_name.capitalize()

        document_category_id.lastupdated_by = f"{user.first_name} {user.last_name}"
        document_category_id.save()
        messages.success(request, "Document Category Updated successfully")
        return HttpResponseRedirect(reverse("emp_add_documentcategory"))


@login_required
def delete_documentcategory(request, id):
    documentcategory = get_object_or_404(DocumentCategory, id=id)
    documentcategory.delete()
    messages.success(
        request, f"{documentcategory.Document_category} deleted successfully.."
    )
    return redirect("emp_add_documentcategory")


######################################### DOCUMENT  #################################################


@login_required
def add_document(request):
    document = Document.objects.all().order_by("-id")
    documentcategory = DocumentCategory.objects.all()
    user = request.user
    dep = user.employee.department
    form = DocumentForm(request.POST or None)

    if form.is_valid():
        document_name = form.cleaned_data["document_name"]
        user = request.user
        form.instance.lastupdated_by = user
        if Document.objects.filter(document_name__iexact=document_name).exists():
            messages.error(request, "This Document already exists.")
        else:
            form.save()
            messages.success(request, "Document added successfully")
            return HttpResponseRedirect(reverse("emp_add_document"))

    context = {
        "form": form,
        "document": document,
        "documentcategory": documentcategory,
        "dep": dep,
    }
    return render(request, "Employee/mastermodule/Document/Document.html", context)


@login_required
def documentupdate_view(request):
    user = request.user
    if request.method == "POST":
        document_category_id = request.POST.get("document_category_id")
        document_name = request.POST.get("document_name")
        document_size = request.POST.get("document_size")
        document_name_id = request.POST.get("document_name_id")

        document_category = DocumentCategory.objects.get(id=document_category_id)
        document = Document.objects.get(id=document_name_id)

        document.document_category_id = document_category
        document.document_name = document_name
        document.document_size = document_size

        user = request.user
        document.lastupdated_by = user
        document.save()
        messages.success(request, "Document Updated successfully")
        return HttpResponseRedirect(reverse("emp_add_document"))


@login_required
def delete_document(request, id):
    document = get_object_or_404(Document, id=id)
    document.delete()
    messages.success(request, f"{document.document_name} deleted successfully..")
    return redirect("emp_add_document")


################################# CASE CATEGORY DOCUMENT #########################################


class CaseCategoryDocumentCreateView(LoginRequiredMixin, CreateView):
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm
    template_name = (
        "Employee/mastermodule/CaseCategoryDocument/addcasecategorydocument.html"
    )
    success_url = reverse_lazy("emp_CaseCategoryDocument_list")

    def form_valid(self, form):
        instance = form.save(commit=False)

        instance.last_updated_by = self.request.user
        instance.save()

        messages.success(self.request, "CaseCategoryDocument Added Successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "Country Document Already exists.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


class CaseCategoryDocumentListView(LoginRequiredMixin, ListView):
    model = CaseCategoryDocument
    template_name = (
        "Employee/mastermodule/CaseCategoryDocument/casecategorydocumentlist.html"
    )
    context_object_name = "CaseCategoryDocument"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context

    def get_queryset(self):
        return CaseCategoryDocument.objects.order_by("-id")


class editCaseCategoryDocument(LoginRequiredMixin, UpdateView):
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm
    template_name = (
        "Employee/mastermodule/CaseCategoryDocument/editcasecategorydocument.html"
    )
    success_url = reverse_lazy("emp_CaseCategoryDocument_list")

    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        form.save()
        messages.success(self.request, "CaseCategoryDocument Updated Successfully.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "Country Document Already exist.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


@login_required
def delete_casecategorydocument(request, id):
    casecategorydocument = get_object_or_404(CaseCategoryDocument, id=id)
    casecategorydocument.delete()
    messages.success(request, "CaseCategory Document deleted successfully..")
    return redirect("emp_CaseCategoryDocument_list")


######################################### BRANCH #################################################


@login_required
def add_branch(request):
    branch = Branch.objects.all().order_by("-id")
    user = request.user
    dep = user.employee.department
    form = BranchForm(request.POST or None)

    if form.is_valid():
        branch_name = form.cleaned_data["branch_name"]
        user = request.user
        form.instance.last_updated_by = user
        if Branch.objects.filter(branch_name__iexact=branch_name).exists():
            messages.error(request, "This Branch already exists.")
        else:
            form.save()
            messages.success(request, "Branch added successfully")
            return HttpResponseRedirect(reverse("emp_add_branch"))

    context = {"form": form, "branch": branch, "dep": dep}
    return render(request, "Employee/mastermodule/Branch/BranchList.html", context)


@login_required
def branchupdate_view(request):
    user = request.user
    if request.method == "POST":
        branch_name = request.POST.get("branch_name")
        branch_source = request.POST.get("branch_source")
        branch_name_id = request.POST.get("branch_name_id")

        branch = Branch.objects.get(id=branch_name_id)

        branch.branch_name = branch_name
        branch.branch_source = branch_source
        branch.last_updated_by = user
        branch.save()
        messages.success(request, "Branch Updated successfully")
        return HttpResponseRedirect(reverse("emp_add_branch"))


@login_required
def delete_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    branch.delete()
    messages.success(request, f"{branch.branch_name} deleted successfully..")
    return redirect("emp_add_branch")


######################################### GROUP #################################################


class CreateGroupView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "Employee/mastermodule/Manage Groups/addgroup.html"
    success_url = reverse_lazy("emp_Group_list")

    def form_valid(self, form):
        form.instance.create_by = self.request.user
        form.save()

        messages.success(self.request, "Group Added Successfully.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "Employee/mastermodule/Manage Groups/grouplist.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context

    def get_queryset(self):
        return Group.objects.order_by("-id")


class editGroup(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "Employee/mastermodule/Manage Groups/updategroup.html"
    success_url = reverse_lazy("emp_Group_list")

    def form_valid(self, form):
        form.instance.create_by = self.request.user

        # Display a success message
        messages.success(self.request, "Group Updated Successfully.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


@login_required
def delete_group(request, id):
    group = get_object_or_404(Group, id=id)
    group.delete()
    messages.success(request, f"{group.group_name} deleted successfully..")
    return redirect("emp_Group_list")


######################################### COURIER #################################################


class PersonalDetailsView(LoginRequiredMixin, CreateView):
    def get(self, request):
        user = self.request.user
        dep = user.employee.department
        form = CompanyCourierDetailsForm()
        return render(
            request,
            "Employee/mastermodule/CourierDetails/companydetails.html",
            {"form": form, "dep": dep},
        )

    def post(self, request):
        form = CompanyCourierDetailsForm(request.POST)
        if form.is_valid():
            # Save personal details to session or another storage mechanism
            request.session["employee_personal_details"] = form.cleaned_data
            return redirect("employee_receiver_details")

        return render(
            request,
            "Employee/mastermodule/CourierDetails/otherdetails.html",
            {"form": form},
        )


class ReceiverDetailsView(LoginRequiredMixin, CreateView):
    def get(self, request):
        user = self.request.user
        dep = user.employee.department
        form = ReceiverDetailsForm()
        return render(
            request,
            "Employee/mastermodule/CourierDetails/otherdetails.html",
            {"form": form, "dep": dep},
        )

    def post(self, request):
        form = ReceiverDetailsForm(request.POST)
        if form.is_valid():
            # Retrieve personal details from session
            personal_details = request.session.get("employee_personal_details", {})

            # Merge personal details with receiver details
            merged_data = {**personal_details, **form.cleaned_data}

            # Save the merged data to the database
            courier_address = CourierAddress(**merged_data)
            courier_address.lastupdated_by = self.request.user
            courier_address.save()
            messages.success(request, "Courier Address added successfully")

            return redirect("emp_viewcourieraddress_list")

        return render(
            request,
            "Employee/mastermodule/CourierDetails/otherdetails.html",
            {"form": form},
        )


@login_required
def viewcourieraddress_list(request):
    courier_addss = CourierAddress.objects.all().order_by("-id")
    user = request.user
    dep = user.employee.department
    context = {"courier_addss": courier_addss, "dep": dep}
    return render(
        request, "Employee/mastermodule/CourierDetails/Courierdetail.html", context
    )


class UpdateCompanyDetailsView(LoginRequiredMixin, View):
    template_name = "Employee/mastermodule/CourierDetails/editcompanydetails.html"

    def get(self, request, id):
        courier_address = CourierAddress.objects.get(id=id)
        user = self.request.user
        dep = user.employee.department
        company_form = CompanyCourierDetailsForm(instance=courier_address)
        return render(
            request,
            self.template_name,
            {
                "company_form": company_form,
                "courier_address": courier_address,
                "dep": dep,
            },
        )

    def post(self, request, id):
        user = self.request.user
        courier_address = CourierAddress.objects.get(id=id)
        company_form = CompanyCourierDetailsForm(request.POST, instance=courier_address)
        if company_form.is_valid():
            courier_address.lastupdated_by = f"{user.first_name} {user.last_name}"
            company_form.save()
            return redirect("emp_update_receiver_details", id=id)
        return render(
            request,
            self.template_name,
            {"company_form": company_form, "courier_address": courier_address},
        )


class UpdateReceiverDetailsView(LoginRequiredMixin, View):
    template_name = "Employee/mastermodule/CourierDetails/editotherdetails.html"

    def get(self, request, id):
        courier_address = CourierAddress.objects.get(id=id)
        user = self.request.user
        dep = user.employee.department
        receiver_form = ReceiverDetailsForm(instance=courier_address)
        return render(
            request,
            self.template_name,
            {
                "receiver_form": receiver_form,
                "courier_address": courier_address,
                "dep": dep,
            },
        )

    def post(self, request, id):
        user = self.request.user
        courier_address = CourierAddress.objects.get(id=id)
        receiver_form = ReceiverDetailsForm(request.POST, instance=courier_address)
        if receiver_form.is_valid():
            courier_address.lastupdated_by = f"{user.first_name} {user.last_name}"
            receiver_form.save()
            messages.success(request, "Courier Address Updated successfully")
            return redirect("emp_viewcourieraddress_list")
        return render(
            request,
            self.template_name,
            {"receiver_form": receiver_form, "courier_address": courier_address},
        )


@login_required
def delete_courierdetails(request, id):
    courier = get_object_or_404(CourierAddress, id=id)
    courier.delete()
    messages.success(request, "CourierAddress deleted successfully..")
    return redirect("emp_viewcourieraddress_list")


# --------------------- Import Branch -----------------------


@login_required
def import_branch(request):
    if request.method == "POST":
        file = request.FILES["file"]
        path = str(file)

        try:
            df = pd.read_excel(file)

            for index, row in df.iterrows():
                branch_name = row["branch_name"].capitalize()
                branch_source = row["branch_source"].upper()

                branch, created = Branch.objects.get_or_create(
                    branch_name=branch_name,
                    branch_source=branch_source,
                )

                if created:
                    branch.save()

            messages.success(request, "Data Imported Successfully!!")

        except Exception as e:
            messages.warning(request, e)
            return redirect("emp_add_branch")
    return redirect("emp_add_branch")


######################################### EMPLOYEE #################################################


@login_required
def add_employee(request):
    branches = Branch.objects.all()
    groups = Group.objects.all()
    user = request.user
    dep = user.employee.department

    if request.method == "POST":
        department = request.POST.get("department")
        emp_code = request.POST.get("emp_code")
        branch_id = request.POST.get("branch_id")
        group_id = request.POST.get("group_id")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = "123456"
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zipcode = request.POST.get("zipcode")
        api_key = request.POST.get("api_key")
        authorization = request.POST.get("authorization")
        tata_tele_agent_no = request.POST.get("tata_tele_agent_no")
        files = request.FILES.get("file")

        if not branch_id:
            messages.warning(request, "Branch ID is required")
            return redirect("emp_emp_personal_details")

        try:
            branchh = Branch.objects.get(id=branch_id)
            group = Group.objects.get(id=group_id)
            if Employee.objects.filter(contact_no__iexact=contact).exists():
                messages.error(request, "Contact No. already exists.")
                return redirect("emp_emp_personal_details")
            if Employee.objects.filter(emp_code__iexact=emp_code).exists():
                messages.error(request, "Employee Code already exists.")
                return redirect("emp_emp_personal_details")
            if CustomUser.objects.filter(email__iexact=email).exists():
                messages.error(request, "Email Address already Register...")
                return redirect("emp_emp_personal_details")
            user = CustomUser.objects.create_user(
                username=email,
                first_name=firstname,
                last_name=lastname,
                email=email,
                password=password,
                user_type="3",
            )

            user.employee.department = department
            user.employee.emp_code = emp_code
            user.employee.branch = branchh
            user.employee.group = group
            user.employee.contact_no = contact
            user.employee.country = country
            user.employee.state = state
            user.employee.City = city
            user.employee.Address = address
            user.employee.zipcode = zipcode
            user.employee.tata_tele_api_key = api_key
            user.employee.tata_tele_authorization = authorization
            user.employee.tata_tele_agent_number = tata_tele_agent_no
            user.employee.file = files

            user.save()
            msg = f"New Employee Added({firstname} {lastname} ({user.employee.department}))"
            create_admin_notification(msg)

            current_count = Notification.objects.filter(is_seen=False).count()
            send_notification_admin(msg, current_count)

            subject = "Congratulations! Your Account is Created"
            message = (
                f"Hello {firstname} {lastname},\n\n"
                f"Welcome to SSDC \n\n"
                f"Congratulations! Your account has been successfully created as an agent.\n\n"
                f" Your id is {email} and your password is {password}.\n\n"
                f" go to login : https://crm.theskytrails.com/ \n\n"
                f"Thank you for joining us!\n\n"
                f"Best regards,\nThe Sky Trails"
            )

            recipient_list = [email]

            # send_mail(subject, message, from_email=None, recipient_list=recipient_list)
            send_congratulatory_email(
                firstname, lastname, email, password, user_type="3"
            )
            messages.success(
                request,
                "Employee Added Successfully , Congratulation Mail Send Successfully!!",
            )

            mobile = contact
            message = (
                f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                f" Hello {firstname} {lastname}, \n\n"
                f" Welcome to Sky Trails! Your Employee account is ready to roll. \n\n"
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

            return redirect("emp_emp_list")

        except Exception as e:
            messages.warning(request, str(e))
            return redirect("emp_emp_personal_details")

    context = {"branch": branches, "group": groups, "dep": dep}
    return render(request, "Employee/Employee Management/addemp1.html", context)


class all_employee(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "Employee/Employee Management/Employeelist.html"
    context_object_name = "employee"

    def get_queryset(self):
        return Employee.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep

        return context


@login_required
def employee_update(request, pk):
    employee = Employee.objects.get(pk=pk)
    user = request.user
    dep = user.employee.department
    context = {"employee": employee, "dep": dep}

    return render(request, "Employee/Employee Management/editemp1.html", context)


@login_required
def employee_update_save(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        department = request.POST.get("department")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zipcode = request.POST.get("zipcode")

        authorization = request.POST.get("authorization")
        api_key = request.POST.get("api_key")
        tata_tele_agent_no = request.POST.get("tata_tele_agent_no")
        file = request.FILES.get("file")

        user = CustomUser.objects.get(id=employee_id)

        user.first_name = firstname
        user.last_name = lastname
        user.email = email
        user.employee.department = department
        user.employee.contact_no = contact
        user.employee.country = country
        user.employee.state = state
        user.employee.City = city
        user.employee.Address = address
        user.employee.zipcode = zipcode

        user.employee.tata_tele_authorization = authorization
        user.employee.tata_tele_api_key = api_key
        user.employee.tata_tele_agent_number = tata_tele_agent_no

        if file:
            user.employee.file = file
        user.save()
        messages.success(request, "Employee Updated Successfully")
        return redirect("emp_emp_list")


@login_required
def delete_employee(request, id):
    try:
        employee = get_object_or_404(Employee, id=id)
        custom_user = employee.users
        custom_user.delete()

        employee.delete()

        messages.success(request, "Employee Deleted Successfully ")
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found")

    return HttpResponseRedirect(reverse("emp_emp_list"))


########################################################## PRICING ##########################################################################


@login_required
def add_subcategory(request):
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    user = request.user
    dep = user.employee.department

    context = {"country": country, "category": category, "dep": dep}

    if request.method == "POST":
        country_id = request.POST.get("country")
        category_id = request.POST.get("category")
        subcategory_name = request.POST.get("subcategory")
        amount = float(request.POST.get("amount") or 0)
        cgst = float(request.POST.get("cgst") or 0)
        sgst = float(request.POST.get("sgst") or 0)
        user = request.user

        # try:
        # Calculate the totalAmount
        total = amount + ((amount * (cgst + sgst)) / 100)

        pricing = VisaSubcategory.objects.create(
            country_id_id=country_id,
            category_id_id=category_id,
            subcategory_name_id=subcategory_name,
            estimate_amt=amount,
            cgst=cgst,
            sgst=sgst,
            totalAmount=total,
            lastupdated_by=f"{user.first_name} {user.last_name}",
        )
        pricing.save()

        messages.success(request, "Pricing Added Successfully !!")
        return redirect("emp_subcategory_list")
        # except Exception as e:
        #     # Handle any exceptions here and possibly log them
        #     # messages.error(request, str(e))
        #     print("eeee",e)

    return render(request, "Employee/mastermodule/Pricing/add_pricing.html", context)


@login_required
def subcategory_list(request):
    user = request.user
    dep = user.employee.department
    subcategory = VisaSubcategory.objects.all().order_by("-id")
    context = {"subcategory": subcategory, "dep": dep}
    return render(request, "Employee/mastermodule/Pricing/pricing.html", context)


@login_required
def visa_subcategory_edit(request, id):
    instance = VisaSubcategory.objects.get(id=id)
    user = request.user
    dep = user.employee.department

    if request.method == "POST":
        form = VisasubCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            user = request.user
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
            form.instance.totalAmount = form.instance.estimate_amt + (
                (form.instance.estimate_amt * (form.instance.cgst + form.instance.sgst))
                / 100
            )
            form.save()
            messages.success(request, "Subcategory updated successfully.")
            return redirect("emp_subcategory_list")
    else:
        form = VisasubCategoryForm(instance=instance)

    return render(
        request,
        "Employee/mastermodule/pricing/edit_pricing.html",
        {"form": form, "dep": dep},
    )


@login_required
def delete_pricing(request, id):
    pricing = VisaSubcategory.objects.get(id=id)
    pricing.delete()
    messages.success(request, "Pricing deleted successfully..")
    return HttpResponseRedirect(reverse("emp_subcategory_list"))


class PackageCreateView(LoginRequiredMixin, CreateView):
    model = Package
    form_class = PackageForm
    template_name = "Employee/Product/addproduct.html"
    success_url = reverse_lazy("Employee_Package_list")

    def form_valid(self, form):
        try:
            form.instance.last_updated_by = self.request.user
            form.save()
            messages.success(
                self.request,
                "Package Added Successfully & Send To Admin for Approval .",
            )
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error: {e}")
            print("Error Occured ", e)
            return self.form_invalid(form)


########################################### NEWS #####################################################


class NewsList(LoginRequiredMixin, ListView):
    model = News
    template_name = "Employee/News/newslist.html"
    context_object_name = "news"

    def get_queryset(self):
        return News.objects.filter(employee=True).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep
        return context


########################################## SUCCESSSTORY ################################################


class SuccessStoryList(LoginRequiredMixin, ListView):
    model = SuccessStory
    template_name = "Employee/SuccessStory/successstorylist.html"
    context_object_name = "story"

    def get_queryset(self):
        return SuccessStory.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dep = user.employee.department
        context["dep"] = dep
        return context


def empPackageApply(request, id):
    print("sssssssssssss")
    if request.method == "POST":
        print("worminggg")
        package = Package.objects.get(id=id)
        package_id = package.id
        request.session["package_id"] = package_id

        return redirect("empPackageEnquiryForm1")


def empPackageEnquiryForm1(request):
    country_choices = Enquiry._meta.get_field("Country").get_choices()

    # request.session["package_id"] = package_id
    package_id = request.session.get("package_id")
    if request.method == "POST":
        country = request.POST.get("country")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        country = request.POST.get("country")
        passport_no = request.POST.get("passport_no")

        request.session["country"] = country
        request.session["first_name"] = first_name
        request.session["last_name"] = last_name
        request.session["email"] = email
        request.session["contact"] = contact
        request.session["dob"] = dob
        request.session["gender"] = gender
        request.session["passport_no"] = passport_no
        return redirect("emp_packageenquiry_form2")

    context = {"country_choices": country_choices}
    return render(request, "Employee/Enquiry/Package Leads/lead1.html", context)


def empPackageEnquiry2View(request):
    if request.method == "POST":
        spouse_name = request.POST.get("spouse_name")
        spouse_contact = request.POST.get("spouse_contact")
        spouse_email = request.POST.get("spouse_email")
        spouse_passport = request.POST.get("spouse_passport")
        spouse_dob = request.POST.get("spouse_dob")
        spouse_relation = request.POST.get("spouse_relation")

        spouse_name1 = request.POST.get("spouse_name1")
        spouse_contact1 = request.POST.get("spouse_contact1")
        spouse_email1 = request.POST.get("spouse_email1")
        spouse_passport1 = request.POST.get("spouse_passport1")
        spouse_dob1 = request.POST.get("spouse_dob1")
        spouse_relation1 = request.POST.get("spouse_relation1")

        spouse_name2 = request.POST.get("spouse_name2")
        spouse_contact2 = request.POST.get("spouse_contact2")
        spouse_email2 = request.POST.get("spouse_email2")
        spouse_passport2 = request.POST.get("spouse_passport2")
        spouse_dob2 = request.POST.get("spouse_dob2")
        spouse_relation2 = request.POST.get("spouse_relation2")

        spouse_name3 = request.POST.get("spouse_name3")
        spouse_contact3 = request.POST.get("spouse_contact3")
        spouse_email3 = request.POST.get("spouse_email3")
        spouse_passport3 = request.POST.get("spouse_passport3")
        spouse_dob3 = request.POST.get("spouse_dob3")
        spouse_relation3 = request.POST.get("spouse_relation3")

        spouse_name4 = request.POST.get("spouse_name4")
        spouse_contact4 = request.POST.get("spouse_contact4")
        spouse_email4 = request.POST.get("spouse_email4")
        spouse_passport4 = request.POST.get("spouse_passport4")
        spouse_dob4 = request.POST.get("spouse_dob4")
        spouse_relation4 = request.POST.get("spouse_relation4")

        spouse_name5 = request.POST.get("spouse_name5")
        spouse_contact5 = request.POST.get("spouse_contact5")
        spouse_email5 = request.POST.get("spouse_email5")
        spouse_passport5 = request.POST.get("spouse_passport5")
        spouse_dob5 = request.POST.get("spouse_dob5")
        spouse_relation5 = request.POST.get("spouse_relation5")

        request.session["spouse_name"] = spouse_name
        request.session["spouse_contact"] = spouse_contact
        request.session["spouse_email"] = spouse_email
        request.session["spouse_passport"] = spouse_passport
        request.session["spouse_dob"] = spouse_dob
        request.session["spouse_relation"] = spouse_relation

        request.session["spouse_name1"] = spouse_name1
        request.session["spouse_contact1"] = spouse_contact1
        request.session["spouse_email1"] = spouse_email1
        request.session["spouse_passport1"] = spouse_passport1
        request.session["spouse_dob1"] = spouse_dob1
        request.session["spouse_relation1"] = spouse_relation1

        request.session["spouse_name2"] = spouse_name2
        request.session["spouse_contact2"] = spouse_contact2
        request.session["spouse_email2"] = spouse_email2
        request.session["spouse_passport2"] = spouse_passport2
        request.session["spouse_dob2"] = spouse_dob2
        request.session["spouse_relation2"] = spouse_relation2

        request.session["spouse_name3"] = spouse_name3
        request.session["spouse_contact3"] = spouse_contact3
        request.session["spouse_email3"] = spouse_email3
        request.session["spouse_passport3"] = spouse_passport3
        request.session["spouse_dob3"] = spouse_dob3
        request.session["spouse_relation3"] = spouse_relation3

        request.session["spouse_name4"] = spouse_name4
        request.session["spouse_contact4"] = spouse_contact4
        request.session["spouse_email4"] = spouse_email4
        request.session["spouse_passport4"] = spouse_passport4
        request.session["spouse_dob4"] = spouse_dob4
        request.session["spouse_relation4"] = spouse_relation4

        request.session["spouse_name5"] = spouse_name5
        request.session["spouse_contact5"] = spouse_contact5
        request.session["spouse_email5"] = spouse_email5
        request.session["spouse_passport5"] = spouse_passport5
        request.session["spouse_dob5"] = spouse_dob5
        request.session["spouse_relation5"] = spouse_relation5
        return redirect("emp_packageenquiry_form3")
    return render(request, "Employee/Enquiry/Package Leads/lead2.html")


def emp_PackageEnquiry3View(request):
    visa_type = Enquiry._meta.get_field("Visa_type").get_choices()
    source = Enquiry._meta.get_field("Source").get_choices()

    package_id = request.session.get("package_id")
    package = Package.objects.get(id=package_id)
    visa_contry_id = package.visa_country.id
    visa_category_id = package.visa_category.id
    visa_country = VisaCountry.objects.get(id=visa_contry_id)
    visa_category = VisaCategory.objects.get(id=visa_category_id)
    dob = request.session.get("dob")

    if request.method == "POST":
        visa_typ = request.POST.get("visa_type")
        source = request.POST.get("source")
        reference = request.POST.get("reference")

        # ----------------------- Enquiry Detailss ------------------
        country = request.session.get("country")
        first_name = request.session.get("first_name")
        last_name = request.session.get("last_name")
        email = request.session.get("email")
        contact = request.session.get("contact")
        dob = request.session.get("dob")
        gender = request.session.get("gender")
        passport_no = request.session.get("passport_no")

        # -------------------------------- Spouse Details ------------------
        spouse_name = request.session.get("spouse_name")
        spouse_contact = request.session.get("spouse_contact")
        spouse_email = request.session.get("spouse_email")
        spouse_passport = request.session.get("spouse_passport")
        spouse_dob = request.session.get("spouse_dob")
        spouse_relation = request.session.get("spouse_relation")

        spouse_name1 = request.session.get("spouse_name1")
        spouse_contact1 = request.session.get("spouse_contact1")
        spouse_email1 = request.session.get("spouse_email1")
        spouse_passport1 = request.session.get("spouse_passport1")
        spouse_dob1 = request.session.get("spouse_dob1")
        spouse_relation1 = request.session.get("spouse_relation1")

        spouse_name2 = request.session.get("spouse_name2")
        spouse_contact2 = request.session.get("spouse_contact2")
        spouse_email2 = request.session.get("spouse_email2")
        spouse_passport2 = request.session.get("spouse_passport2")
        spouse_dob2 = request.session.get("spouse_dob2")
        spouse_relation2 = request.session.get("spouse_relation2")

        spouse_name3 = request.session.get("spouse_name3")
        spouse_contact3 = request.session.get("spouse_contact3")
        spouse_email3 = request.session.get("spouse_email3")
        spouse_passport3 = request.session.get("spouse_passport3")
        spouse_dob3 = request.session.get("spouse_dob3")
        spouse_relation3 = request.session.get("spouse_relation3")

        spouse_name4 = request.session.get("spouse_name4")
        spouse_contact4 = request.session.get("spouse_contact4")
        spouse_email4 = request.session.get("spouse_email4")
        spouse_passport4 = request.session.get("spouse_passport4")
        spouse_dob4 = request.session.get("spouse_dob4")
        spouse_relation4 = request.session.get("spouse_relation4")

        spouse_name5 = request.session.get("spouse_name5")
        spouse_contact5 = request.session.get("spouse_contact5")
        spouse_email5 = request.session.get("spouse_email5")
        spouse_passport5 = request.session.get("spouse_passport5")
        spouse_dob5 = request.session.get("spouse_dob5")
        spouse_relation5 = request.session.get("spouse_relation5")

        enq = Enquiry.objects.create(
            FirstName=first_name,
            LastName=last_name,
            email=email,
            contact=contact,
            Dob=dob,
            Gender=gender,
            Country=country,
            passport_no=passport_no,
            spouse_name=spouse_name,
            spouse_no=spouse_contact,
            spouse_passport=spouse_passport,
            spouse_relation=spouse_relation,
            spouse_name1=spouse_name1,
            spouse_no1=spouse_contact1,
            spouse_passport1=spouse_passport1,
            spouse_relation1=spouse_relation1,
            spouse_name2=spouse_name2,
            spouse_no2=spouse_contact2,
            spouse_passport2=spouse_passport2,
            spouse_relation2=spouse_relation2,
            spouse_name3=spouse_name3,
            spouse_no3=spouse_contact3,
            spouse_passport3=spouse_passport3,
            spouse_relation3=spouse_relation3,
            spouse_name4=spouse_name4,
            spouse_no4=spouse_contact4,
            spouse_passport4=spouse_passport4,
            spouse_relation4=spouse_relation4,
            spouse_name5=spouse_name5,
            spouse_no5=spouse_contact5,
            spouse_passport5=spouse_passport5,
            spouse_relation5=spouse_relation5,
            Source=source,
            Reference=reference,
            Visa_type=visa_typ,
            Package=package,
            Visa_country=visa_country,
            Visa_category=visa_category,
        )
        user = request.user

        if spouse_email:
            enq.spouse_email = spouse_email
        if spouse_email1:
            enq.spouse_email1 = spouse_email1

        if spouse_email2:
            enq.spouse_email2 = spouse_email2
        if spouse_email3:
            enq.spouse_email3 = spouse_email3
        if spouse_email4:
            enq.spouse_email4 = spouse_email4
        if spouse_email5:
            enq.spouse_email5 = spouse_email5

        if spouse_dob:
            enq.spouse_dob = spouse_dob
        if spouse_dob1:
            enq.spouse_dob1 = spouse_dob1
        if spouse_dob2:
            enq.spouse_dob2 = spouse_dob2
        if spouse_dob3:
            enq.spouse_dob3 = spouse_dob3
        if spouse_dob4:
            enq.spouse_dob4 = spouse_dob4
        if spouse_dob5:
            enq.spouse_dob5 = spouse_dob5

        enq.created_by = user

        enq.save()
        messages.success(request, "Enquiry Added successfully")
        return redirect("emp_enquiry_form4", enq.id)

    context = {
        "package_id": package_id,
        "package": package,
        "visa_type": visa_type,
        "source": source,
    }
    return render(request, "Employee/Enquiry/Package Leads/lead3.html", context)


# ---------------------------------- Appointment ----------------------------


def emp_appointment(request):
    user = request.user.employee
    all_events = Appointment.objects.filter(employee=user)

    context = {"events": all_events}
    return render(request, "Employee/Appointment/appointment.html", context)


def all_appointment(request):
    user = request.user.employee
    all_events = Appointment.objects.filter(employee=user)
    print("demooooooooooooo", all_events)
    out = []
    for event in all_events:
        formatted_date = event.start.strftime("%Y-%m-%d")
        out.append(
            {
                "title": event.name,
                "id": event.id,
                "start": event.start.strftime("%Y-%m-%dT%H:%M:%S"),
                "time": event.time,
            }
        )
    return JsonResponse(out, safe=False)


def add_appointment(request):
    user = request.user.employee
    start = request.GET.get("start", None)
    end = request.GET.get("time", None)
    time = request.GET.get("time", None)
    title = request.GET.get("title", None)
    event = Appointment(employee=user, name=str(title), start=start, time=time)
    event.save()
    data = {}
    return JsonResponse(data)


def update(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)
    id = request.GET.get("id", None)

    event = Appointment.objects.get(id=id)
    event.start = start
    event.name = title
    event.save()
    data = {}
    return JsonResponse(data)


def remove(request):
    id = request.GET.get("id", None)
    event = Appointment.objects.get(id=id)
    event.delete()
    data = {}
    return JsonResponse(data)


# --------------------------------- Todo ------------------------------


def emp_add_todo(request):
    description = request.POST.get("todoDescription")

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        task = Todo.objects.create(user=request.user, description=description)

        return HttpResponseRedirect(reverse("employee_dashboard"))
    except Exception as e:
        pass


def emp_update_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        description = request.POST.get("todoDescription")

        todo.description = description
        todo.save()

        return HttpResponseRedirect(reverse("employee_dashboard"))
    except Exception as e:
        pass


def emp_delete_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields

        todo.delete()

        return HttpResponseRedirect(reverse("employee_dashboard"))
    except Exception as e:
        pass


def color_code(request):
    if request.method == "POST":
        enq_id = request.POST.get("enq_id")
        color_code = request.POST.get("color_code")  # Corrected this line
        enquiry = Enquiry.objects.get(id=enq_id)
        enquiry.color_code = color_code
        enquiry.save()
        messages.success(request, f"Lead Color {color_code} Updated Successfully...")
        return redirect("emp_enrolleddocument", id=enq_id)


############################################# RAR #############################################################


import os
import tempfile
import zipfile
import requests
import logging
import mimetypes
from django.http import HttpResponse

logger = logging.getLogger(__name__)


@login_required
def download_all_documents(request, id):
    enq = Enquiry.objects.get(id=id)
    doc_files = DocumentFiles.objects.filter(enquiry_id=enq)

    # Collect document URLs
    document_urls = [
        request.build_absolute_uri(doc_file.document_file.url)
        for doc_file in doc_files
        if doc_file.document_file
    ]

    logger.info(f"Document URLs: {document_urls}")

    # Create a temporary directory to store the files
    temp_dir = tempfile.mkdtemp()

    try:
        # Download each document to the temporary directory
        for index, document_url in enumerate(document_urls):
            response = requests.get(document_url, stream=True)
            content_type = response.headers.get(
                "Content-Type", "application/octet-stream"
            )  # Get the content type

            if response.status_code == 200:
                # Determine file extension based on content type
                file_extension = get_file_extension(content_type)
                document_path = os.path.join(
                    temp_dir, f"document_{index + 1}{file_extension}"
                )
                with open(document_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=128):
                        file.write(chunk)
            else:
                logger.warning(f"Failed to download document from {document_url}")

        # Create the ZIP archive
        zip_file_path = os.path.join(temp_dir, "documents.zip")
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for index, document_url in enumerate(document_urls):
                response = requests.head(document_url)
                content_type = response.headers.get(
                    "Content-Type", "application/octet-stream"
                )
                file_extension = get_file_extension(content_type)
                document_path = os.path.join(
                    temp_dir, f"document_{index + 1}{file_extension}"
                )
                if os.path.exists(document_path):
                    archive.write(document_path, os.path.basename(document_path))
                else:
                    logger.warning(f"Document file not found: {document_path}")

        # Serve the ZIP archive for download
        with open(zip_file_path, "rb") as archive_file:
            response = HttpResponse(archive_file.read(), content_type="application/zip")
            response["Content-Disposition"] = f"attachment; filename=documents.zip"
            return response

    except Exception as e:
        logger.error(f"Error during download_all_documents: {e}")
        raise  # Reraise the exception to see the traceback in the console

    finally:
        # Clean up temporary files and directory
        for file_path in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file_path)
            os.remove(file_path)
        os.rmdir(temp_dir)


def get_file_extension(content_type):
    extension = mimetypes.guess_extension(content_type, strict=False)
    return extension if extension else ".dat"


@login_required
def search_enquiries(request):
    user = request.user

    if user.is_authenticated:
        if user.user_type == "3":
            emp = user.employee
            dep = emp.department
            if dep == "Presales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Sales":
                enq = Enquiry.objects.filter(
                    Q(assign_to_sales_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")

            elif dep == "Documentation":
                enq = Enquiry.objects.filter(
                    Q(assign_to_documentation_employee=user.employee)
                    | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Visa Team":
                enq = Enquiry.objects.filter(
                    Q(assign_to_visa_team_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            elif dep == "Assesment":
                enq = Enquiry.objects.filter(
                    Q(assign_to_assesment_employee=user.employee) | Q(created_by=user)
                ).order_by("-id")
            else:
                enq = Enquiry.objects.filter(created_by=request.user)

    if request.method == "POST":
        enquiry_id = request.POST.get("enquiry_id")
        name = request.POST.get("name")
        dob = request.POST.get("date_of_birth")
        passport_no = request.POST.get("passport_no")
        Package = request.POST.get("package")
        lead_status = request.POST.get("lead_status")
        color_code = request.POST.get("color_code")
        created_by = request.POST.get("created_by")
        Visa_country = request.POST.get("Visa_country")

        filter_conditions = Q()

        if enquiry_id:
            filter_conditions &= Q(enquiry_number__icontains=enquiry_id)

        if name:
            names = name.split()

            first_name_condition = Q()
            last_name_condition = Q()

            for n in names:
                first_name_condition |= Q(FirstName__icontains=n)
                last_name_condition |= Q(LastName__icontains=n)

            filter_conditions &= first_name_condition & last_name_condition

        if dob:
            filter_conditions &= Q(Dob=dob)

        if passport_no:
            filter_conditions &= Q(passport_no__icontains=passport_no)

        if Package:
            filter_conditions &= Q(Package_title__icontains=Package)

        if lead_status and lead_status != "Select":
            filter_conditions &= Q(lead_status=lead_status)

        if color_code and color_code != "Select":
            filter_conditions &= Q(color_code=color_code)

        if created_by:
            created_bys = created_by.split()

            first_name_condition = Q()
            last_name_condition = Q()

            for n in created_bys:
                first_name_condition |= Q(created_by__first_name__icontains=n)
                last_name_condition |= Q(created_by__last_name__icontains=n)

            filter_conditions &= first_name_condition & last_name_condition

        if Visa_country:
            filter_conditions &= Q(Visa_country__country__icontains=Visa_country)

        if filter_conditions:
            enq = enq.filter(filter_conditions)

    return render(request, "Employee/Enquiry/lead_list.html", {"enq": enq})


@login_required
def submit(request):
    if request.method == "POST":
        enq_id = request.POST.get("enq_id")
        enq = Enquiry.objects.get(id=enq_id)
        user = request.user
        emp_dep = user.employee
        if emp_dep.department == "Presales":
            enq.assign_to_employee = request.user.employee

        elif emp_dep.department == "Assesment":
            lat_assigned_index = cache.get("lst_assigned_index") or 0
            presale_employees = get_presale_employee()
            if presale_employees.exists():
                next_index = (lat_assigned_index + 1) % presale_employees.count()
                enq.assign_to_employee = presale_employees[next_index]
                enq.assign_to_assesment_employee = request.user.employee

                cache.set("lst_assigned_index", next_index)

        elif emp_dep.department == "Sales":
            lat_assigned_index = cache.get("lst_assigned_index") or 0
            presale_employees = get_presale_employee()
            if presale_employees.exists():
                next_index = (lat_assigned_index + 1) % presale_employees.count()
                enq.assign_to_employee = presale_employees[next_index]
                enq.assign_to_sales_employee = request.user.employee

                cache.set("lst_assigned_index", next_index)

        elif emp_dep.department == "Documentation":
            last_assigned_index = cache.get("last_assigned_index") or 0
            visa_employees = get_visa_team_employee()
            if visa_employees.exists():
                next_index = (last_assigned_index + 1) % visa_employees.count()
                enq.assign_to_visa_team_employee = visa_employees[next_index]
                enq.assign_to_documentation_employee = request.user.employee

                cache.set("last_assigned_index", next_index)
        elif emp_dep.department == "Visa Team":
            last_assigned_index = cache.get("last_assigned_index") or 0
            presale_employees = get_presale_employee()
            if presale_employees.exists():
                next_index = (last_assigned_index + 1) % presale_employees.count()
                enq.assign_to_employee = presale_employees[next_index]
                enq.assign_to_documentation_employee = request.user.employee

                cache.set("last_assigned_index", next_index)
        enq.save()
        return redirect("employee_lead_list")


def lead_emp_add_agent(request):
    logged_in_user = request.user
    relevant_employees = Employee.objects.all()
    user = request.user

    dep = user.employee.department

    if request.method == "POST":
        type = request.POST.get("type")

        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = request.POST.get("password")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zipcode = request.POST.get("zipcode")
        files = request.FILES.get("files")

        existing_agent = CustomUser.objects.filter(username=email)
        fullname = str(firstname + " " + lastname)
        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return redirect("emp_add_agent")

            if type == "Outsourcing Partner":
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="5",
                )
                logged_in_user = request.user

                user.outsourcingagent.type = type
                user.outsourcingagent.contact_no = contact
                user.outsourcingagent.country = country
                user.outsourcingagent.state = state
                user.outsourcingagent.City = city
                user.outsourcingagent.Address = address
                user.outsourcingagent.zipcode = zipcode
                user.outsourcingagent.profile_pic = files
                user.outsourcingagent.registerdby = logged_in_user
                user.outsourcingagent.assign_employee = logged_in_user.employee
                chat_group_name = f"{fullname} Group"
                chat_group = ChatGroup.objects.create(
                    group_name=chat_group_name,
                )
                chat_group.group_member.add(user.outsourcingagent.assign_employee.users)
                chat_group.group_member.add(user)

                user.save()

                # create_admin_notification("New Lead Added")
                msg = f"New OutSourceAgent Added({fullname})"
                create_admin_notification(msg)

                current_count = Notification.objects.filter(is_seen=False).count()
                send_notification_admin(msg, current_count)
                # send_notification_admin("New Lead Assign Added", current_count)

                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an Outsource Agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com/Agent/Login/ \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )

                recipient_list = [email]

                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="5"
                )

                mobile_number = contact

                message = (
                    f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                    f" Hello {firstname} {lastname}, \n\n"
                    f" Welcome to Sky Trails! Your OutsourceAgent account is ready to roll. \n\n"
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
                response = send_whatsapp_message(mobile_number, message)

                messages.success(request, "OutSource Agent Added Successfully")
                return redirect("emp_all_outsource_agent")

            else:
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="4",
                )
                logged_in_user = request.user

                user.agent.type = type
                user.agent.contact_no = contact
                user.agent.country = country
                user.agent.state = state
                user.agent.City = city
                user.agent.Address = address
                user.agent.zipcode = zipcode
                user.agent.profile_pic = files
                user.agent.registerdby = logged_in_user
                user.agent.assign_employee = logged_in_user.employee
                chat_group_name = f"{fullname} Group"
                chat_group = ChatGroup.objects.create(
                    group_name=chat_group_name,
                )
                chat_group.group_member.add(user.agent.assign_employee.users)
                chat_group.group_member.add(user)
                user.save()

                msg = f"New Agent Added({fullname})"
                create_admin_notification(msg)

                current_count = Notification.objects.filter(is_seen=False).count()
                send_notification_admin(msg, current_count)

                context = {"employees": relevant_employees, "dep": dep}

                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com/Agent/Login/ \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )

                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="4"
                )

                mobile_number = contact

                message = (
                    f"🌟 Welcome to Sky Trails - Your Account Details 🌟 \n\n"
                    f" Hello {firstname} {lastname}, \n\n"
                    f" Welcome to Sky Trails! Your Agent account is ready to roll. \n\n"
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
                response = send_whatsapp_message(mobile_number, message)

                messages.success(request, "Agent Added Successfully")
                return redirect("emp_enquiry_form1")

        except Exception as e:
            messages.warning(request, e)

    context = {"employees": relevant_employees, "dep": dep}

    return render(request, "Employee/Agent Management/addagent.html", context)
