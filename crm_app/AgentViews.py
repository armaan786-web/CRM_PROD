from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .models import *
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    TemplateView,
)
from django.views import View
from .forms import *
from django.db.models import Prefetch
from django.urls import reverse_lazy
from django.contrib import messages
import requests
from datetime import datetime
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count, Case, When, IntegerField, Q
from .notifications import (
    create_notification,
    send_notification,
    assign_notification,
    create_notification_agent,
    assignop_notification,
    create_notification_outsourceagent,
    create_admin_notification,
    send_notification_admin,
)


class agent_dashboard(LoginRequiredMixin, TemplateView):
    template_name = "Agent/Dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enq_enrolled_count = 0
        enq_count = 0

        leadaccept_count = Enquiry.objects.filter(
            Q(lead_status="Enrolled")
            | Q(lead_status="Inprocess")
            | Q(lead_status="Ready To Submit")
            | Q(lead_status="Appointment")
            | Q(lead_status="Ready To Collection")
            | Q(lead_status="Result")
            | Q(lead_status="Delivery"),
            created_by=self.request.user,
        ).count()

        lead_count = Enquiry.objects.filter(created_by=self.request.user).count()

        package = Package.objects.filter(approval="True").order_by("-last_updated_on")[
            :10
        ]

        story = SuccessStory.objects.all()

        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()

        if user.user_type == "4":
            agent = Agent.objects.get(users=user)
            latest_news = News.objects.filter(agent=True).order_by("-created_at")[:10]
            context["agent"] = agent
            context["latest_news"] = latest_news
            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_agent=user.agent,
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
                    Q(assign_to_agent=user.agent) | Q(created_by=user)
                )
                .values(
                    "id", "registered_on"
                )  # Include the id to ensure distinct on Enquiry objects
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(
                    count=Count("id", distinct=True)
                )  # Count only distinct Enquiry objects
                .order_by("month__month")
            )
            if all_enq.exists():
                enq_count = all_enq[0]["count"]

        if user.user_type == "5":
            outagent = OutSourcingAgent.objects.get(users=user)
            news = News.objects.filter(outsource_Agent=True).order_by("-created_at")[
                :10
            ]
            context["agent"] = outagent
            context["latest_news"] = news

            enrolled_monthly_counts = (
                Enquiry.objects.filter(
                    Q(
                        lead_status="Enrolled",
                        assign_to_outsourcingagent=user.outsourcingagent,
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
                    Q(assign_to_outsourcingagent=user.outsourcingagent)
                    | Q(created_by=user)
                )
                .values(
                    "id", "registered_on"
                )  # Include the id to ensure distinct on Enquiry objects
                .annotate(month=TruncMonth("registered_on"))
                .values("month")
                .annotate(
                    count=Count("id", distinct=True)
                )  # Count only distinct Enquiry objects
                .order_by("month__month")
            )

            if all_enq.exists():
                enq_count = all_enq[0]["count"]
        todo = Todo.objects.filter(user=self.request.user).order_by("-id")

        context["leadaccept_count"] = leadaccept_count
        context["lead_count"] = lead_count
        context["package"] = package
        context["faq_count"] = faq_count
        context["story"] = story
        context["enrolled_monthly_counts"] = enrolled_monthly_counts
        context["enq_enrolled_count"] = enq_enrolled_count
        context["all_enq"] = all_enq
        context["enq_count"] = enq_count
        context["todo"] = todo

        return context


# class agent_dashboard(TemplateView):
#     template_name = "Agent/Dashboard/dashboard.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         leadaccept_count = Enquiry.objects.filter(
#             Q(lead_status="Enrolled")
#             | Q(lead_status="Inprocess")
#             | Q(lead_status="Ready To Submit")
#             | Q(lead_status="Appointment")
#             | Q(lead_status="Ready To Collection")
#             | Q(lead_status="Result")
#             | Q(lead_status="Delivery"),
#             created_by=self.request.user,
#         ).count()

#         lead_count = Enquiry.objects.filter(created_by=self.request.user).count()

#         package = Package.objects.filter(approval="True").order_by("-last_updated_on")[
#             :10
#         ]

#         user = self.request.user
#         faq_count = FAQ.objects.filter(user=user).count()

#         if user.user_type == "4":
#             agent = Agent.objects.get(users=user)
#             context["agent"] = agent

#             outagent = OutSourcingAgent.objects.get(users=user)
#             context["agent"] = outagent
#             enrolled_monthly_counts = (
#                 Enquiry.objects.filter(
#                     Q(
#                         lead_status="Enrolled",
#                         assign_to_agent=user.agent,
#                     )
#                     | Q(lead_status="Enrolled", created_by=user)
#                 )
#                 .annotate(month=TruncMonth("registered_on"))
#                 .values("month")
#                 .annotate(count=Count("id"))
#                 .order_by("month__month")
#             )
#             if enrolled_monthly_counts.exists():
#                 enq_enrolled_count = enrolled_monthly_counts[0]["count"]

#             all_enq = (
#                 Enquiry.objects.filter(
#                     Q(assign_to_agent=user.agent) | Q(created_by=user)
#                 )
#                 .values(
#                     "id", "registered_on"
#                 )  # Include the id to ensure distinct on Enquiry objects
#                 .annotate(month=TruncMonth("registered_on"))
#                 .values("month")
#                 .annotate(
#                     count=Count("id", distinct=True)
#                 )  # Count only distinct Enquiry objects
#                 .order_by("month__month")
#             )
#             if all_enq.exists():
#                 enq_count = all_enq[0]["count"]

#         if user.user_type == "5":
#             outagent = OutSourcingAgent.objects.get(users=user)
#             context["agent"] = outagent
#             enrolled_monthly_counts = (
#                 Enquiry.objects.filter(
#                     Q(
#                         lead_status="Enrolled",
#                         assign_to_outsourcingagent=user.outsourcingagent,
#                     )
#                     | Q(lead_status="Enrolled", created_by=user)
#                 )
#                 .annotate(month=TruncMonth("registered_on"))
#                 .values("month")
#                 .annotate(count=Count("id"))
#                 .order_by("month__month")
#             )
#             if enrolled_monthly_counts.exists():
#                 enq_enrolled_count = enrolled_monthly_counts[0]["count"]

#             all_enq = (
#                 Enquiry.objects.filter(
#                     Q(assign_to_outsourcingagent=user.outsourcingagent)
#                     | Q(created_by=user)
#                 )
#                 .values(
#                     "id", "registered_on"
#                 )  # Include the id to ensure distinct on Enquiry objects
#                 .annotate(month=TruncMonth("registered_on"))
#                 .values("month")
#                 .annotate(
#                     count=Count("id", distinct=True)
#                 )  # Count only distinct Enquiry objects
#                 .order_by("month__month")
#             )
#             if all_enq.exists():
#                 enq_count = all_enq[0]["count"]

#         context["leadaccept_count"] = leadaccept_count
#         context["lead_count"] = lead_count
#         context["package"] = package
#         context["faq_count"] = faq_count
#         context["enrolled_monthly_counts"] = enrolled_monthly_counts
#         context["enq_enrolled_count"] = enq_enrolled_count
#         context["all_enq"] = all_enq
#         context["enq_count"] = enq_count

#         return context


############################################### LEADS ##########################################################


class Enquiry1View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm1()
        user = request.user
        faq_count = FAQ.objects.filter(user=user).count()
        return render(
            request,
            "Agent/Enquiry/lead1.html",
            {"form": form, "faq_count": faq_count},
        )

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
            request.session["agent_enquiry_form1"] = cleaned_data
            return redirect("agent_enquiry_form2")

        return render(
            request,
            "Agent/Enquiry/lead2.html",
            {"form": form},
        )


class Enquiry2View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm2()
        user = request.user
        faq_count = FAQ.objects.filter(user=user).count()
        return render(
            request,
            "Agent/Enquiry/lead2.html",
            {"form": form, "faq_count": faq_count},
        )

    def post(self, request):
        form = EnquiryForm2(request.POST)
        if form.is_valid():
            # Retrieve personal details from session
            enquiry_form1 = request.session.get("agent_enquiry_form1", {})

            # Safely retrieve spouse_dob and format it if available
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
            request.session["agent_enquiry_form2"] = merged_data
            return redirect("agent_enquiry_form3")

        return render(
            request,
            "Agent/Enquiry/lead2.html",
            {"form": form},
        )


class Enquiry3View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm3()
        user = request.user
        faq_count = FAQ.objects.filter(user=user).count()
        return render(
            request,
            "Agent/Enquiry/lead3.html",
            {"form": form, "faq_count": faq_count},
        )

    def post(self, request):
        form1_data = request.session.get("agent_enquiry_form1", {})
        form2_data = request.session.get("agent_enquiry_form2", {})
        form3 = EnquiryForm3(request.POST)

        if form3.is_valid():
            user = self.request.user

            # Merge data from all three forms
            merged_data = {
                **form1_data,
                **form2_data,
                **form3.cleaned_data,
            }

            # Save the merged data to the database
            enquiry = Enquiry(**merged_data)
            # ---------------------------------------

            # ------------------------------
            enquiry.created_by = user
            if user.user_type == "5":
                enquiry.assign_to_outsourcingagent = user.outsourcingagent
            enquiry.lead_status = "New Lead"
            enquiry.save()
            messages.success(request, "Enquiry Added successfully")

            # Clear session data after successful submission
            request.session.pop("agent_enquiry_form1", None)
            request.session.pop("agent_enquiry_form2", None)

            return redirect("agent_enquiry_form4", id=enquiry.id)

        return render(
            request,
            "Agent/Enquiry/lead3.html",
            {"form": form3},
        )

    def get_success_url(self):
        enquiry_id = self.object.id
        return reverse_lazy("agent_enquiry_form4", kwargs={"id": enquiry_id})


@login_required
def agentdocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()
    user = request.user
    faq_count = FAQ.objects.filter(user=user).count()

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
        "faq_count": faq_count,
    }

    return render(request, "Agent/Enquiry/lead4.html", context)


def upload_document(request):
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
        return redirect("agent_enquiry_form4", enq_id)


@login_required
def delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("agent_enquiry_form4", enqq)


# ----------------------------------- Leads Details --------------------------


def agent_new_leads_details(request):
    user = request.user
    excluded_statuses = ["Accept", "Case Initiated"]
    lead = [status for status in leads_status if status[0] not in excluded_statuses]

    faq_count = FAQ.objects.filter(user=user).count()
    user_type = user.user_type
    if user_type == "5":
        enquiry = Enquiry.objects.filter(
            Q(assign_to_outsourcingagent=user.outsourcingagent) | Q(created_by=user)
        ).order_by("-id")
    elif user_type == "4":
        enquiry = Enquiry.objects.filter(
            Q(assign_to_agent=user.agent) | Q(created_by=user)
        ).order_by("-id")

    context = {"enquiry": enquiry, "faq_count": faq_count, "lead": lead}

    return render(request, "Agent/Enquiry/lead-details.html", context)


def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        data = response.json()
        return data["ip"]
    except Exception as e:
        # Handle the exception (e.g., log the error)
        return None


@login_required
def agent_add_notes(request):
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

    return redirect("agent_new_leads_details")


def resend(request, id):
    enq_id = Enquiry.objects.get(id=id)
    enq_id.lead_status = "Active"
    enq_id.save()
    return redirect("agent_new_leads_details")


@login_required
def edit_enrolled_application(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    user = request.user
    faq_count = FAQ.objects.filter(user=user).count()
    # form = FollowUpForm()
    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "faq_count": faq_count,
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

        return redirect("agent_education_summary", id=id)

    return render(
        request,
        "Agent/Enquiry/Enrolled Enquiry/Editenrolledpart1.html",
        context,
    )


@login_required
def combined_view(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    education_summary = Education_Summary.objects.filter(enquiry_id=enquiry).first
    work_exp = Work_Experience.objects.filter(enquiry_id=enquiry).first
    bk_info = Background_Information.objects.filter(enquiry_id=enquiry).first
    user = request.user
    faq_count = FAQ.objects.filter(user=user).count()
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

        return redirect("agent_edit_product_details", id=id)

    test_scores = TestScore.objects.filter(enquiry_id=enquiry)

    context = {
        "enquiry": enquiry,
        "test_scores": test_scores,
        "education_summary": education_summary,
        "work_exp": work_exp,
        "bk_info": bk_info,
        "faq_count": faq_count,
    }

    return render(
        request, "Agent/Enquiry/Enrolled Enquiry/Editenrolledpart2.html", context
    )


@login_required
def delete_test_score(request, id):
    test_score = TestScore.objects.get(id=id)
    enquiry_id = test_score.enquiry_id.id
    test_score.delete()
    return redirect("agent_education_summary", id=enquiry_id)


@login_required
def editproduct_details(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    product = Package.objects.all()
    user = request.user
    faq_count = FAQ.objects.filter(user=user).count()
    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "product": product,
        "faq_count": faq_count,
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

        return redirect("agent_enrolled_document", id=id)

    return render(
        request,
        "Agent/Enquiry/Enrolled Enquiry/Editenrolledpart3.html",
        context,
    )


@login_required
def enrolleddocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

    doc_file = DocumentFiles.objects.filter(enquiry_id=enq)
    user = request.user
    faq_count = FAQ.objects.filter(user=user).count()

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
        "faq_count": faq_count,
    }

    return render(
        request, "Agent/Enquiry/Enrolled Enquiry/Editenrolledpart4.html", context
    )


def enrolled_upload_document(request):
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
        return redirect("agent_enrolled_document", id=enq_id)


@login_required
def enrolled_delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("agent_enrolled_document", enqq)


########################################### PRODUCT ######################################################


class PackageDetailView(LoginRequiredMixin, DetailView):
    model = Package
    template_name = "Agent/Product/Productdetails.html"
    context_object_name = "package"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        return context


def agent_PackageApplyView(request, id):
    if request.method == "POST":
        package = Package.objects.get(id=id)
        package_id = package.id

        request.session["package_id"] = package_id

        return redirect("agent_packageenquiry_form1")


class PackageListView(LoginRequiredMixin, ListView):
    model = Package
    template_name = "Agent/Product/product.html"
    context_object_name = "Package"

    def get_queryset(self):
        return Package.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        return context


############################################ QUERIES ######################################################


class FAQCreateView(LoginRequiredMixin, CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = "Agent/Queries/add_query.html"
    success_url = reverse_lazy("resolved_queries")

    def form_valid(self, form):
        form.instance.user = self.request.user

        user = self.request.user.agent
        form.instance.employee = user.assign_employee

        messages.success(self.request, "FAQ Added Successfully.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        return context


class ResolvedFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Agent/Queries/resolvedquery.html"
    context_object_name = "resolved_queries"

    def get_queryset(self):
        return (
            FAQ.objects.filter(user=self.request.user)
            .exclude(answer="")
            .exclude(answer__isnull=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_queries_count"] = self.get_pending_queries_count(
            self.request.user
        )
        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        return context

    def get_pending_queries_count(self, user):
        return (
            FAQ.objects.filter(user=user, answer__exact="")
            .exclude(answer__isnull=True)
            .count()
        )


class PendingFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Agent/Queries/quries.html"
    context_object_name = "pending_queries"

    def get_queryset(self):
        return FAQ.objects.filter(user=self.request.user, answer__exact="").exclude(
            answer__isnull=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_queries_count"] = self.get_queryset().count()
        user = self.request.user
        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        return context


###################################### LOGOUT #######################################################


@login_required
def agent_logout(request):
    user = request.user
    user.is_logged_in = False
    user.save()
    logout(request)
    return redirect("/")


############################################### CHANGE PASSWORD ###########################################


@login_required
def ChangePassword(request):
    user = request.user
    admin = Agent.objects.get(users=user)

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

    return render(request, "Agent/Dashboard/dashboard.html")


class profileview(TemplateView, LoginRequiredMixin):
    template_name = "Agent/Profile/Profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = Enquiry.objects.filter(created_by=self.request.user)
        completedleads = Enquiry.objects.filter(
            lead_status="Delivery", created_by=self.request.user
        )

        user = self.request.user
        if user.user_type == "4":
            agent = Agent.objects.get(users=user)
            context["agent"] = agent

        if user.user_type == "5":
            outagent = OutSourcingAgent.objects.get(users=user)
            context["agent"] = outagent

        if hasattr(user, "get_user_type_display"):
            context["user_type"] = user.get_user_type_display()

        faq_count = FAQ.objects.filter(user=user).count()
        context["faq_count"] = faq_count
        context["leads"] = leads
        context["completedleads"] = completedleads
        context["faq_count"] = faq_count

        return context


@login_required
def edit_profile(request):
    users = request.user
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        # email = request.POST.get('email')
        contact = request.POST.get("contact")

        if users.user_type == "4":
            agent_instance = Agent.objects.get(users=request.user)

            agent_instance.users.first_name = first_name
            agent_instance.users.last_name = last_name
            # agent_instance.users.email = email
            agent_instance.contact_no = contact

            agent_instance.users.save()
            agent_instance.save()

        elif users.user_type == "5":
            outsource_instance = OutSourcingAgent.objects.get(users=request.user)

            outsource_instance.users.first_name = first_name
            outsource_instance.users.last_name = last_name
            # outsource_instance.users.email = email
            outsource_instance.contact_no = contact

            outsource_instance.users.save()
            outsource_instance.save()

        return redirect("Agent_profile")

    return render(request, "Agent/Profile/Profile.html")


################################################# APPOINTMENT ###################################################


class AppointmentListView(LoginRequiredMixin, ListView):
    model = EnqAppointment
    template_name = "Agent/Appointment/appointmentlist.html"
    context_object_name = "appointment"

    def get_queryset(self):
        user = self.request.user
        user_enquiries = Enquiry.objects.filter(created_by=user)
        user_appointments = EnqAppointment.objects.filter(
            enquiry__in=user_enquiries
        ).order_by("-id")
        return user_appointments


class AppointmentGridView(LoginRequiredMixin, ListView):
    model = EnqAppointment
    template_name = "Agent/Appointment/appointmentgrid.html"
    context_object_name = "appointment"

    def get_queryset(self):
        user = self.request.user
        user_enquiries = Enquiry.objects.filter(created_by=user)
        user_appointments = EnqAppointment.objects.filter(
            enquiry__in=user_enquiries
        ).order_by("-id")
        return user_appointments


class PackageCreateView(LoginRequiredMixin, CreateView):
    model = Package
    form_class = PackageForm
    template_name = "Admin/Product/addproduct.html"
    success_url = reverse_lazy("Agent_Package_list")

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

            return self.form_invalid(form)


########################################### NEWS #####################################################


class NewsList(LoginRequiredMixin, ListView):
    model = News
    template_name = "Agent/News/newslist.html"
    context_object_name = "news"

    def get_queryset(self):
        user = self.request.user

        if user.user_type == "4":
            return News.objects.filter(agent=True).order_by("-id")

        elif user.user_type == "5":
            return News.objects.filter(outsource_Agent=True).order_by("-id")


########################################## SUCCESSSTORY ################################################


class SuccessStoryList(LoginRequiredMixin, ListView):
    model = SuccessStory
    template_name = "Agent/SuccessStory/successstorylist.html"
    context_object_name = "story"

    def get_queryset(self):
        return SuccessStory.objects.all().order_by("-id")


@login_required
def create_report(request):
    if request.method == "POST":
        notes = request.POST.get("notes")

        user = request.user

        report = Report.objects.create(
            user=user, notes=notes, created_at=timezone.now()
        )

        messages.success(request, "Complain Added Successfully & Sent To Admin.")
        return redirect("agent_dashboard")

    return render(request, "Agent/Dashboard/dashboard.html")


class ReportList(LoginRequiredMixin, ListView):
    model = Report
    template_name = "Agent/Report/report.html"
    context_object_name = "report"

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).order_by("-id")


def agent_PackageEnquiry1View(request):
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
        return redirect("agent_packageenquiry_form2")

    context = {"country_choices": country_choices}
    return render(request, "Agent/Enquiry/Package Leads/lead1.html", context)


def agent_PackageEnquiry2View(request):
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
        return redirect("agent_packageenquiry_form3")
    return render(request, "Agent/Enquiry/Package Leads/lead2.html")


def agent_PackageEnquiry3View(request):
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
        enq.created_by = request.user
        enq.save()
        return redirect("agent_enquiry_form4", enq.id)

    context = {
        "package_id": package_id,
        "package": package,
        "visa_type": visa_type,
        "source": source,
    }
    return render(request, "Agent/Enquiry/Package Leads/lead3.html", context)


########################################### STATUS UPDATE #################################################


def agent_lead_updated(request, id):
    if request.method == "POST":
        lead_status = request.POST.get("lead_status")
        enquiry = Enquiry.objects.get(id=id)
        enquiry.lead_status = lead_status
        enquiry.save()
        return HttpResponseRedirect(reverse("agent_new_leads_details"))


# --------------------------------- Todo ------------------------------


def Agent_add_todo(request):
    description = request.POST.get("todoDescription")

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        task = Todo.objects.create(user=request.user, description=description)

        return HttpResponseRedirect(reverse("agent_dashboard"))
    except Exception as e:
        pass


def Agent_update_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        description = request.POST.get("todoDescription")

        todo.description = description
        todo.save()

        return HttpResponseRedirect(reverse("agent_dashboard"))
    except Exception as e:
        pass


def Agent_delete_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields

        todo.delete()

        return HttpResponseRedirect(reverse("agent_dashboard"))
    except Exception as e:
        pass


@login_required
def submit(request):
    if request.method == "POST":
        enq_id = request.POST.get("enq_id")
        enq = Enquiry.objects.get(id=enq_id)
        user = request.user
        if user.user_type == "4":
            last_assigned_index = cache.get("last_assigned_index") or 0
            # If no student is assigned, find the next available student in a circular manner
            presales_team_employees = Employee.objects.filter(department="Presales")

            if presales_team_employees.exists():
                next_index = (last_assigned_index + 1) % presales_team_employees.count()
                enq.assign_to_employee = presales_team_employees[next_index]
                enq.assign_to_employee.save()

                cache.set("last_assigned_index", next_index)
                create_notification(enq.assign_to_employee, "New Lead Assign Added")

                current_count = Notification.objects.filter(
                    is_seen=False, employee=enq.assign_to_employee
                ).count()

                employee_id = enq.assign_to_employee.id
                send_notification(employee_id, "New Lead Assign Added", current_count)

                create_admin_notification("New Lead Added")

                current_count = Notification.objects.filter(is_seen=False).count()
                send_notification_admin("New Lead Assign Added", current_count)

        enq.save()
        return redirect("agent_new_leads_details")
