from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import *
from django.urls import reverse
from django.db.models import Q
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    TemplateView,
)
from django.views import View
from django.urls import reverse_lazy
import pandas as pd

# from .whatsapp_api import send_whatsapp_message
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Prefetch
import requests
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import authenticate, logout, login as auth_login
from .SMSAPI.whatsapp_api import send_whatsapp_message, send_sms_message

# from wkhtmltopdf.utils import render_to_pdf_response
from wkhtmltopdf.views import PDFTemplateResponse
from .Email.email_utils import send_congratulatory_email, send_package_email
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .notifications import (
    create_notification,
    send_notification,
    assign_notification,
    create_notification_agent,
    assignop_notification,
    create_notification_outsourceagent,
)

######################################### COUNTRY #################################################


class admin_dashboard(LoginRequiredMixin, TemplateView):
    template_name = "Admin/Dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        enq_count = 0
        enq_enrolled_count = 0
        agent_count = Agent.objects.count()

        outsourceagent_count = OutSourcingAgent.objects.count()

        total_agent_count = agent_count + outsourceagent_count

        employee_count = Employee.objects.count()

        leadarchive_count = Enquiry.objects.filter(archive="True").count()

        leadaccept_count = Enquiry.objects.filter(lead_status="Enrolled").count()

        leadinprocess_count = Enquiry.objects.filter(
            Q(lead_status="Inprocess") | Q(lead_status="Ready To Submit")
        ).count()

        leadappoint_count = Enquiry.objects.filter(
            Q(lead_status="Appointment") | Q(lead_status="Ready To Collection")
        ).count()

        completed_count = Enquiry.objects.filter(lead_status="Delivery").count()

        leadpending_count = Enquiry.objects.filter(lead_status="Active").count()

        leadtotal_count = Enquiry.objects.all().count()

        leadnew_count = Enquiry.objects.filter(lead_status="New Lead").count()
        leadresult_count = Enquiry.objects.filter(lead_status="Result").count()

        package = Package.objects.filter(approval="True").order_by("-last_updated_on")[
            :10
        ]

        active_users = CustomUser.objects.filter(is_logged_in=True).count()
        active_employee = CustomUser.objects.filter(user_type="3", is_logged_in=True)
        active_agent = CustomUser.objects.filter(
            user_type__in=["4", "5"], is_logged_in=True
        )

        story = SuccessStory.objects.all()

        latest_news = News.objects.order_by("-created_at")[:10]

        enrolled_monthly_counts = (
            Enquiry.objects.filter(lead_status="Enrolled")
            .annotate(month=TruncMonth("registered_on"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month__month")
        )
        if enrolled_monthly_counts.exists():
            enq_enrolled_count = enrolled_monthly_counts[0]["count"]

        all_enq = (
            Enquiry.objects.all()
            .annotate(month=TruncMonth("registered_on"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month__month")
        )
        todo = Todo.objects.filter(user=self.request.user).order_by("-id")

        if all_enq.exists():
            enq_count = all_enq[0]["count"]

        context["total_agent_count"] = total_agent_count
        context["employee_count"] = employee_count
        context["leadarchive_count"] = leadarchive_count
        context["leadaccept_count"] = leadaccept_count
        context["leadpending_count"] = leadpending_count
        context["leadtotal_count"] = leadtotal_count
        context["leadnew_count"] = leadnew_count
        context["package"] = package
        context["enrolled_monthly_counts"] = enrolled_monthly_counts
        context["all_enq"] = all_enq
        context["enq_count"] = enq_count
        context["enq_enrolled_count"] = enq_enrolled_count
        context["story"] = story
        context["latest_news"] = latest_news
        context["todo"] = todo
        context["active_users"] = active_users
        context["active_employee"] = active_employee
        context["active_agent"] = active_agent
        context["leadinprocess_count"] = leadinprocess_count
        context["leadappoint_count"] = leadappoint_count
        context["completed_count"] = completed_count
        context["leadresult_count"] = leadresult_count

        return context


@login_required
def add_visacountry(request):
    visacountry = VisaCountry.objects.all().order_by("-id")
    form = VisaCountryForm(request.POST or None)

    if form.is_valid():
        country_name = form.cleaned_data["country"]
        user = request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        if VisaCountry.objects.filter(country__iexact=country_name).exists():
            messages.error(request, "This country already exists.")
        else:
            form.save()
            messages.success(request, "Visa Country added successfully")
            return HttpResponseRedirect(reverse("add_visacountry"))

    context = {"form": form, "visacountry": visacountry}
    return render(request, "Admin/mastermodule/VisaCountry/VisaCountry.html", context)


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
        return HttpResponseRedirect(reverse("add_visacountry"))


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
            return redirect("add_visacountry")
    return redirect("add_visacountry")


@login_required
def delete_visa_country(request, id):
    visacountry_id = VisaCountry.objects.get(id=id)
    visacountry_id.delete()
    messages.success(request, f"{visacountry_id.country} deleted successfully..")
    return HttpResponseRedirect(reverse("add_visacountry"))


######################################### CATEGORY #################################################


@login_required
def add_visacategory(request):
    visacategory = VisaCategory.objects.all().order_by("-id")
    country = VisaCountry.objects.all()
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
                return HttpResponseRedirect(reverse("add_visacategory"))

    context = {"form": form, "visacategory": visacategory, "country": country}
    return render(request, "Admin/mastermodule/VisaCategory/VisaCategory.html", context)


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
        return HttpResponseRedirect(reverse("add_visacategory"))


@login_required
def delete_category(request, id):
    category = get_object_or_404(VisaCategory, id=id)
    category.delete()
    messages.success(request, f"{category.category} deleted successfully..")
    return redirect("add_visacategory")


######################################### DOCUMENT CATEGORY ############################################


@login_required
def add_documentcategory(request):
    documentcategory = DocumentCategory.objects.all().order_by("-id")
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
            return HttpResponseRedirect(reverse("add_documentcategory"))

    context = {"form": form, "documentcategory": documentcategory}
    return render(
        request, "Admin/mastermodule/DocumentCategory/DocumentCategory.html", context
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
        return HttpResponseRedirect(reverse("add_documentcategory"))


@login_required
def delete_documentcategory(request, id):
    documentcategory = get_object_or_404(DocumentCategory, id=id)
    documentcategory.delete()
    messages.success(
        request, f"{documentcategory.Document_category} deleted successfully.."
    )
    return redirect("add_documentcategory")


######################################### DOCUMENT  #################################################


@login_required
def add_document(request):
    document = Document.objects.all().order_by("-id")
    documentcategory = DocumentCategory.objects.all()
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
            return HttpResponseRedirect(reverse("add_document"))

    context = {"form": form, "document": document, "documentcategory": documentcategory}
    return render(request, "Admin/mastermodule/Document/Document.html", context)


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
        return HttpResponseRedirect(reverse("add_document"))


@login_required
def delete_document(request, id):
    document = get_object_or_404(Document, id=id)
    document.delete()
    messages.success(request, f"{document.document_name} deleted successfully..")
    return redirect("add_document")


################################# CASE CATEGORY DOCUMENT #########################################


class CaseCategoryDocumentCreateView(LoginRequiredMixin, CreateView):
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm

    template_name = (
        "Admin/mastermodule/CaseCategoryDocument/addcasecategorydocument.html"
    )
    success_url = reverse_lazy("CaseCategoryDocument_list")

    def form_valid(self, form):
        instance = form.save(commit=False)

        instance.last_updated_by = self.request.user
        instance.save()

        messages.success(self.request, "CaseCategoryDocument Added Successfully.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "Country Document Already exist.")
        return super().form_invalid(form)


class CaseCategoryDocumentListView(LoginRequiredMixin, ListView):
    model = CaseCategoryDocument
    template_name = (
        "Admin/mastermodule/CaseCategoryDocument/casecategorydocumentlist.html"
    )
    context_object_name = "CaseCategoryDocument"

    def get_queryset(self):
        return CaseCategoryDocument.objects.order_by("-id")


class editCaseCategoryDocument(LoginRequiredMixin, UpdateView):
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm
    template_name = (
        "Admin/mastermodule/CaseCategoryDocument/editcasecategorydocument.html"
    )
    success_url = reverse_lazy("CaseCategoryDocument_list")

    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user

        # Display a success message
        messages.success(self.request, "CaseCategoryDocument Updated Successfully.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "Country Document Already exist.")
        return super().form_invalid(form)


@login_required
def delete_casecategorydocument(request, id):
    casecategorydocument = get_object_or_404(CaseCategoryDocument, id=id)
    casecategorydocument.delete()
    messages.success(request, "CaseCategory Document deleted successfully..")
    return redirect("CaseCategoryDocument_list")


######################################### BRANCH #################################################


@login_required
def add_branch(request):
    branch = Branch.objects.all().order_by("-id")
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
            return HttpResponseRedirect(reverse("add_branch"))

    context = {"form": form, "branch": branch}
    return render(request, "Admin/mastermodule/Branch/BranchList.html", context)


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
        return HttpResponseRedirect(reverse("add_branch"))


@login_required
def delete_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    branch.delete()
    messages.success(request, f"{branch.branch_name} deleted successfully..")
    return redirect("add_branch")


######################################### GROUP #################################################


class CreateGroupView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "Admin/mastermodule/Manage Groups/addgroup.html"  # Update with your template name
    success_url = reverse_lazy("Group_list")

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.create_by = self.request.user

        # Display a success message
        messages.success(self.request, "Group Added Successfully.")

        return super().form_valid(form)


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "Admin/mastermodule/Manage Groups/grouplist.html"
    context_object_name = "group"

    def get_queryset(self):
        return Group.objects.order_by("-id")


class editGroup(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "Admin/mastermodule/Manage Groups/updategroup.html"
    success_url = reverse_lazy("Group_list")

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.create_by = self.request.user

        # Display a success message
        messages.success(self.request, "Group Updated Successfully.")

        return super().form_valid(form)


@login_required
def delete_group(request, id):
    group = get_object_or_404(Group, id=id)
    group.delete()
    messages.success(request, f"{group.group_name} deleted successfully..")
    return redirect("Group_list")


######################################### COURIER #################################################


class PersonalDetailsView(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = CompanyCourierDetailsForm()
        return render(
            request,
            "Admin/mastermodule/CourierDetails/companydetails.html",
            {"form": form},
        )

    def post(self, request):
        form = CompanyCourierDetailsForm(request.POST)
        if form.is_valid():
            # Save personal details to session or another storage mechanism
            request.session["personal_details"] = form.cleaned_data
            return redirect("receiver_details")

        return render(
            request,
            "Admin/mastermodule/CourierDetails/otherdetails.html",
            {"form": form},
        )


class ReceiverDetailsView(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = ReceiverDetailsForm()
        return render(
            request,
            "Admin/mastermodule/CourierDetails/otherdetails.html",
            {"form": form},
        )

    def post(self, request):
        form = ReceiverDetailsForm(request.POST)
        if form.is_valid():
            # Retrieve personal details from session
            personal_details = request.session.get("personal_details", {})

            # Merge personal details with receiver details
            merged_data = {**personal_details, **form.cleaned_data}

            # Save the merged data to the database
            courier_address = CourierAddress(**merged_data)
            courier_address.lastupdated_by = self.request.user
            courier_address.save()
            messages.success(request, "Courier Address added successfully")

            return redirect("viewcourieraddress_list")

        return render(
            request,
            "Admin/mastermodule/CourierDetails/otherdetails.html",
            {"form": form},
        )


@login_required
def viewcourieraddress_list(request):
    courier_addss = CourierAddress.objects.all().order_by("-id")
    context = {"courier_addss": courier_addss}
    return render(
        request, "Admin/mastermodule/CourierDetails/Courierdetail.html", context
    )


class UpdateCompanyDetailsView(LoginRequiredMixin, View):
    template_name = "Admin/mastermodule/CourierDetails/editcompanydetails.html"

    def get(self, request, id):
        courier_address = CourierAddress.objects.get(id=id)
        company_form = CompanyCourierDetailsForm(instance=courier_address)
        return render(
            request,
            self.template_name,
            {"company_form": company_form, "courier_address": courier_address},
        )

    def post(self, request, id):
        user = self.request.user
        courier_address = CourierAddress.objects.get(id=id)
        company_form = CompanyCourierDetailsForm(request.POST, instance=courier_address)
        if company_form.is_valid():
            courier_address.lastupdated_by = f"{user.first_name} {user.last_name}"
            company_form.save()
            return redirect("update_receiver_details", id=id)
        return render(
            request,
            self.template_name,
            {"company_form": company_form, "courier_address": courier_address},
        )


class UpdateReceiverDetailsView(LoginRequiredMixin, View):
    template_name = "Admin/mastermodule/CourierDetails/editotherdetails.html"

    def get(self, request, id):
        courier_address = CourierAddress.objects.get(id=id)
        receiver_form = ReceiverDetailsForm(instance=courier_address)
        return render(
            request,
            self.template_name,
            {"receiver_form": receiver_form, "courier_address": courier_address},
        )

    def post(self, request, id):
        user = self.request.user
        courier_address = CourierAddress.objects.get(id=id)
        receiver_form = ReceiverDetailsForm(request.POST, instance=courier_address)
        if receiver_form.is_valid():
            courier_address.lastupdated_by = f"{user.first_name} {user.last_name}"
            receiver_form.save()
            messages.success(request, "Courier Address Updated successfully")
            return redirect("viewcourieraddress_list")
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
    return redirect("viewcourieraddress_list")


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
            return redirect("add_branch")
    return redirect("add_branch")


######################################### EMPLOYEE #################################################


@login_required
def add_employee(request):
    branches = Branch.objects.all()
    groups = Group.objects.all()
    dep = Department_Choices

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
            return redirect("emp_personal_details")

        try:
            branchh = Branch.objects.get(id=branch_id)
            group = Group.objects.get(id=group_id)
            if Employee.objects.filter(contact_no__iexact=contact).exists():
                messages.error(request, "Contact No. already exists.")
                return redirect("emp_personal_details")
            if Employee.objects.filter(emp_code__iexact=emp_code).exists():
                messages.error(request, "Employee Code already exists.")
                return redirect("emp_personal_details")
            if CustomUser.objects.filter(email__iexact=email).exists():
                messages.error(request, "Email Address already Register...")
                return redirect("emp_personal_details")
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

            return redirect("emp_list")

        except Exception as e:
            messages.warning(request, str(e))
            return redirect("emp_personal_details")

    context = {"branch": branches, "group": groups, "dep": dep}
    return render(request, "Admin/Employee Management/addemp1.html", context)


class all_employee(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "Admin/Employee Management/Employeelist.html"
    context_object_name = "employee"

    def get_queryset(self):
        return Employee.objects.order_by("-id")


@login_required
def employee_update(request, pk):
    employee = Employee.objects.get(pk=pk)
    dep = Department_Choices
    context = {"employee": employee, "dep": dep}

    return render(request, "Admin/Employee Management/editemp1.html", context)


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
        return redirect("emp_list")


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

    return HttpResponseRedirect(reverse("emp_list"))


############################################### AGENT ########################################################


@login_required
def add_agent(request):
    logged_in_user = request.user
    relevant_employees = Employee.objects.all()

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
        fullname = str(firstname + lastname)

        existing_agent = CustomUser.objects.filter(username=email)

        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return redirect("add_agent")

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
                last_assigned_index = cache.get("last_assigned_index") or 0
                sales_team_employees = Employee.objects.filter(department="Sales")
                user.outsourcingagent.type = type
                user.outsourcingagent.contact_no = contact
                user.outsourcingagent.country = country
                user.outsourcingagent.state = state
                user.outsourcingagent.City = city
                user.outsourcingagent.Address = address
                user.outsourcingagent.zipcode = zipcode
                user.outsourcingagent.profile_pic = files
                user.outsourcingagent.registerdby = logged_in_user
                if sales_team_employees.exists():
                    next_index = (
                        last_assigned_index + 1
                    ) % sales_team_employees.count()
                    user.outsourcingagent.assign_employee = sales_team_employees[
                        next_index
                    ]
                    chat_group_name = f"{fullname} Group"
                    chat_group = ChatGroup.objects.create(
                        group_name=chat_group_name,
                        create_by=logged_in_user,
                    )
                    chat_group.group_member.add(
                        user.outsourcingagent.assign_employee.users
                    )  # Add assigned employee
                    chat_group.group_member.add(user)
                    cache.set("last_assigned_index", next_index)
                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="5"
                )
                user.save()

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

                mobile = contact
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
                response = send_whatsapp_message(mobile, message)
                if response.status_code == 200:
                    pass
                else:
                    pass

                messages.success(request, "OutSource Agent Added Successfully")
                return redirect("all_outsource_agent")

            else:
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="4",
                )
                fullname = str(firstname + lastname)
                logged_in_user = request.user
                last_assigned_index = cache.get("last_assigned_index") or 0
                sales_team_employees = Employee.objects.filter(department="Sales")

                user.agent.type = type
                user.agent.contact_no = contact
                user.agent.country = country
                user.agent.state = state
                user.agent.City = city
                user.agent.Address = address
                user.agent.zipcode = zipcode
                user.agent.profile_pic = files
                user.agent.registerdby = logged_in_user
                if sales_team_employees.exists():
                    next_index = (
                        last_assigned_index + 1
                    ) % sales_team_employees.count()
                    user.agent.assign_employee = sales_team_employees[next_index]
                    cache.set("last_assigned_index", next_index)
                    chat_group_name = f"{fullname} Group"
                    chat_group = ChatGroup.objects.create(
                        group_name=chat_group_name,
                        create_by=logged_in_user,
                    )
                    chat_group.group_member.add(
                        user.agent.assign_employee.users
                    )  # Add assigned employee
                    chat_group.group_member.add(user)

                user.save()
                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="4"
                )

                context = {
                    "employees": relevant_employees,
                }

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

                # recipient_list = [email]

                send_congratulatory_email(
                    firstname, lastname, email, password, user_type="4"
                )
                mobile = contact
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

                response = send_whatsapp_message(mobile, message)

                if response.status_code == 200:
                    pass
                else:
                    pass

                messages.success(request, "Agent Added Successfully")
                return redirect("agent_list")

        except Exception as e:
            messages.warning(request, e)

    context = {
        "employees": relevant_employees,
    }

    return render(request, "Admin/Agent Management/addagent.html", context)


class all_agent(LoginRequiredMixin, ListView):
    model = Agent
    template_name = "Admin/Agent Management/agentlist.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_queryset"] = Employee.objects.all()
        return context


class Grid_agent(LoginRequiredMixin, ListView):
    model = Agent
    template_name = "Admin/Agent Management/agentgrid.html"
    context_object_name = "agent"

    def get_queryset(self):
        return Agent.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_queryset"] = Employee.objects.all()
        return context


@login_required
def agent_delete(request, id):
    try:
        agent = Agent.objects.get(id=id)
        custom_user = agent.users
        custom_user.delete()

        agent.delete()

        messages.success(request, "Agent Deleted Successfully ")
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found")

    return HttpResponseRedirect(reverse("agent_list"))


@login_required
def admin_agent_details(request, id):
    agent = Agent.objects.get(id=id)
    users = agent.users

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
        return redirect("admin_agent_details", id)

    context = {"agent": agent}
    return render(request, "Admin/Agent Management/Update/agentupdate.html", context)


@login_required
def admin_agent_agreement(request, id):
    agent = Agent.objects.get(id=id)
    agntagreement = AgentAgreement.objects.filter(agent=agent)
    if request.method == "POST":
        name = request.POST.get("agreement_name")
        file = request.FILES.get("file")
        agreement = AgentAgreement.objects.create(
            agent=agent, agreement_name=name, agreement_file=file
        )
        agreement.save()
        messages.success(request, "Agreement Updated Succesfully...")
        return redirect("admin_agent_agreement", id)
    context = {"agent": agent, "agreement": agntagreement}
    return render(request, "Admin/Agent Management/Update/agentagreement.html", context)


@login_required
def admin_agent_agreement_update(request, id):
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
        return redirect("admin_agent_agreement", agent.id)


@login_required
def admin_agent_agreement_delete(request, id):
    agree = AgentAgreement.objects.get(id=id)
    agent = agree.agent
    agreement = AgentAgreement.objects.get(id=id)
    agreement.delete()
    messages.success(request, "Agreement Deleted Successfully...")
    return redirect("admin_agent_agreement", agent.id)


@login_required
def admin_agent_kyc(request, id):
    agent = Agent.objects.get(id=id)
    kyc_agent = AgentKyc.objects.filter(agent=agent).last

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
            return redirect("admin_agent_kyc", id)

    context = {"agent": agent, "kyc_id": kyc_id, "kyc_agent": kyc_agent}

    return render(request, "Admin/Agent Management/Update/agentkyc.html", context)


@login_required
def admin_agent_delete(request, id):
    agent = Agent.objects.get(id=id)
    kyc_id = AgentKyc.objects.get(agent=agent)


class all_outsource_agent(LoginRequiredMixin, ListView):
    model = OutSourcingAgent
    template_name = "Admin/Agent Management/outsourcelist.html"
    context_object_name = "agentoutsource"

    def get_queryset(self):
        return OutSourcingAgent.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_queryset"] = Employee.objects.all()
        return context


class Grid_outsource_agent(LoginRequiredMixin, ListView):
    model = OutSourcingAgent
    template_name = "Admin/Agent Management/outsorcegrid.html"
    context_object_name = "agentoutsource"

    def get_queryset(self):
        return OutSourcingAgent.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_queryset"] = Employee.objects.all()
        return context


@login_required
def admin_outsourceagent_details(request, id):
    outsourceagent = OutSourcingAgent.objects.get(id=id)
    users = users = outsourceagent.users
    context = {"agent": outsourceagent}
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
        return redirect("admin_outsourceagent_details", id)

    context = {"agent": outsourceagent}
    return render(
        request,
        "Admin/Agent Management/OutsourceUpdate/outsource_agentupdate.html",
        context,
    )


@login_required
def admin_outsource_agent_agreement(request, id):
    outsourceagent = OutSourcingAgent.objects.get(id=id)

    agntagreement = AgentAgreement.objects.filter(outsourceagent=outsourceagent)
    if request.method == "POST":
        name = request.POST.get("agreement_name")
        file = request.FILES.get("file")
        agreement = AgentAgreement.objects.create(
            outsourceagent=outsourceagent, agreement_name=name, agreement_file=file
        )
        agreement.save()
        messages.success(request, "Agreement Updated Succesfully...")
        return redirect("admin_outsource_agent_agreement", id)
    # context = {"agent": agent, "agreement": agntagreement}
    context = {"agent": outsourceagent, "agreement": agntagreement}
    return render(
        request,
        "Admin/Agent Management/OutsourceUpdate/outsource_agentagreement.html",
        context,
    )


@login_required
def admin_outsource_agent_kyc(request, id):
    outsourceagent = OutSourcingAgent.objects.get(id=id)
    outsourcekyc = AgentKyc.objects.filter(outsourceagent=outsourceagent).last

    # context = {"outsourceagent": outsourceagent}

    kyc_id = None

    if request.method == "POST":
        adharfront_file = request.FILES.get("adharfront_file")
        adharback_file = request.FILES.get("adharback_file")
        pan_file = request.FILES.get("pan_file")
        registration_file = request.FILES.get("registration_file")
        try:
            kyc_id = AgentKyc.objects.get(outsourceagent=outsourceagent)

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
                return redirect("admin_outsource_agent_kyc", id)
            else:
                pass

        except AgentKyc.DoesNotExist:
            kyc_id = None
            kyc = AgentKyc.objects.create(
                outsourceagent=outsourceagent,
                adhar_card_front=adharfront_file,
                adhar_card_back=adharback_file,
                pancard=pan_file,
                registration_certificate=registration_file,
            )
            kyc.save()
            messages.success(request, "Kyc Added Successfully..")
            return redirect("admin_outsource_agent_kyc", id)

    context = {"agent": outsourceagent, "kyc_id": kyc_id, "outsourcekyc": outsourcekyc}

    # return render(request, "Admin/Agent Management/Update/agentkyc.html", context)

    return render(
        request,
        "Admin/Agent Management/OutsourceUpdate/outsource_agentkyc.html",
        context,
    )


@login_required
def admin_outsourceagent_agreement_update(request, id):
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
        return redirect("admin_outsource_agent_agreement", outsource.id)


@login_required
def outstsourceagent_delete(request, id):
    try:
        outsourceagent = OutSourcingAgent.objects.get(id=id)
        custom_user = outsourceagent.users
        custom_user.delete()

        outsourceagent.delete()

        messages.success(request, "OutSourceAgent Deleted Successfully ")
    except OutSourcingAgent.DoesNotExist:
        messages.error(request, "OutSourceAgent not found")

    return HttpResponseRedirect(reverse("all_outsource_agent"))


@login_required
def admin_outsource_agent_agreement_delete(request, id):
    agree = AgentAgreement.objects.get(id=id)
    agent = agree.outsourceagent
    agreement = AgentAgreement.objects.get(id=id)
    agreement.delete()
    messages.success(request, "Agreement Deleted Successfully...")
    return redirect("admin_outsource_agent_agreement", agent.id)


###################################################### PACKAGE ###############################################


class PackageCreateView(LoginRequiredMixin, CreateView):
    model = Package
    form_class = PackageForm
    template_name = "Admin/Product/addproduct.html"
    success_url = reverse_lazy("Package_list")

    def form_valid(self, form):
        try:
            form.instance.last_updated_by = self.request.user
            form.instance.approval = "True"
            self.object = form.save()
            self.send_whatsapp_messages()
            self.send_email()

            messages.success(self.request, "Package Added Successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error: {e}")
            return self.form_invalid(form)

    def send_whatsapp_messages(self):
        user_types = ["2", "3", "4", "5", "6"]
        for user_type in user_types:
            users = CustomUser.objects.filter(user_type=user_type)
            for user in users:
                contact = self.get_contact_number(user)
                if contact:
                    title = self.object.title if self.object else None
                    country = (
                        self.object.visa_country.country
                        if (self.object and self.object.visa_country)
                        else None
                    )
                    message = (
                        f"🌟 Greetings User! 🌟 \n\n"
                        f" *We are thrilled to share with you our latest addition to our visa services: * \n\n"
                        f" {title} for {country}.  \n\n"
                        f" This is a great opportunity for you to work in one of the most beautiful and diverse countries in the world. \n\n"
                    )
                    response = send_whatsapp_message(contact, message)
                    if response.status_code == 200:
                        pass
                    else:
                        pass

    def send_email(self):
        title = self.object.title if self.object else None
        country = (
            self.object.visa_country.country
            if (self.object and self.object.visa_country)
            else None
        )

        send_package_email(title, country)

    def get_contact_number(self, user):
        # Method to get the contact number based on user type
        if user.user_type == "2":
            return Admin.objects.get(users=user).contact_no
        elif user.user_type == "3":
            return Employee.objects.get(users=user).contact_no
        elif user.user_type == "4":
            return Agent.objects.get(users=user).contact_no
        elif user.user_type == "5":
            return OutSourcingAgent.objects.get(users=user).contact_no


class PackageListView(LoginRequiredMixin, ListView):
    model = Package
    template_name = "Admin/Product/product.html"
    context_object_name = "Package"

    def get_queryset(self):
        return Package.objects.filter(approval=True).order_by("-id")


class DisapprivePackageListView(LoginRequiredMixin, ListView):
    model = Package
    template_name = "Admin/Product/disapproveproduct.html"
    context_object_name = "Package"

    def get_queryset(self):
        return Package.objects.filter(approval=False).order_by("-id")


class editPackage(LoginRequiredMixin, UpdateView):
    model = Package
    form_class = PackageForm
    template_name = "Admin/Product/editproduct.html"
    success_url = reverse_lazy("Package_list")

    def form_valid(self, form):
        form.instance.lastupdated_by = self.request.user

        messages.success(self.request, "Package Updated Successfully.")

        return super().form_valid(form)


class PackageDetailView(LoginRequiredMixin, DetailView):
    model = Package
    template_name = "Admin/Product/Productdetails.html"
    context_object_name = "package"


def PackageApplyView(request, id):
    if request.method == "POST":
        package = Package.objects.get(id=id)
        package_id = package.id
        request.session["package_id"] = package_id

        return redirect("packageenquiry_form1")


@login_required
def delete_package(request, id):
    package = get_object_or_404(Package, id=id)
    package.delete()
    return redirect("Package_list")


############################################ LOGIN LOGS ######################################################

# -----------------------------------------------


def emp_package_apply(request, id):
    if request.method == "POST":
        package = Package.objects.get(id=id)
        package_id = package.id
        request.session["package_id"] = package_id

        return redirect("packageenquiry_form1")


# ----------------------------------------------
class loginlog(LoginRequiredMixin, ListView):
    model = LoginLog
    template_name = "Admin/Login Logs/Loginlogs.html"
    context_object_name = "loginlog"

    def get_queryset(self):
        return LoginLog.objects.exclude(user__user_type="1").order_by("-id")


########################################################## PRICING ##########################################################################


@login_required
def add_subcategory(request):
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()

    context = {
        "country": country,
        "category": category,
    }

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
        return redirect("subcategory_list")

    return render(request, "Admin/mastermodule/Pricing/add_pricing.html", context)


@login_required
def subcategory_list(request):
    subcategory = VisaSubcategory.objects.all().order_by("-id")
    context = {"subcategory": subcategory}
    return render(request, "Admin/mastermodule/Pricing/pricing.html", context)


@login_required
def visa_subcategory_edit(request, id):
    instance = VisaSubcategory.objects.get(id=id)

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
            return redirect("subcategory_list")
    else:
        form = VisasubCategoryForm(instance=instance)

    return render(
        request, "Admin/mastermodule/pricing/edit_pricing.html", {"form": form}
    )


@login_required
def delete_pricing(request, id):
    pricing = VisaSubcategory.objects.get(id=id)
    pricing.delete()
    messages.success(request, "Pricing deleted successfully..")
    return HttpResponseRedirect(reverse("subcategory_list"))


class Enquiry1View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm1()
        return render(
            request,
            "Admin/Enquiry/lead1.html",
            {"form": form},
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
            request.session["enquiry_form1"] = cleaned_data
            return redirect("enquiry_form2")

        return render(
            request,
            "Admin/Enquiry/lead2.html",
            {"form": form},
        )


class Enquiry2View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm2()
        return render(
            request,
            "Admin/Enquiry/lead2.html",
            {"form": form},
        )

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
            return redirect("enquiry_form3")

        return render(
            request,
            "Admin/Enquiry/lead2.html",
            {"form": form},
        )


class Enquiry3View(LoginRequiredMixin, CreateView):
    def get(self, request):
        form = EnquiryForm3()
        return render(
            request,
            "Admin/Enquiry/lead3.html",
            {"form": form},
        )

    def post(self, request):
        form1_data = request.session.get("enquiry_form1", {})
        form2_data = request.session.get("enquiry_form2", {})
        form3 = EnquiryForm3(request.POST)

        if form3.is_valid():
            user = self.request.user

            # Merge data from all three forms
            merged_data = {
                **form1_data,
                **form2_data,
                **form3.cleaned_data,
            }

            # if "spouse_name" in form2_data:
            #     # Convert the input string into a list for spouse_name
            #     spouse_names = [
            #         item.strip() for item in form2_data["spouse_name"].split(",")
            #     ]
            #     merged_data["spouse_name"] = spouse_names
            # merged_data["spouse_name"] = spouse_names

            # Save the merged data to the database
            enquiry = Enquiry(**merged_data)
            # ---------------------------------------

            last_assigned_index = cache.get("last_assigned_index") or 0
            # If no student is assigned, find the next available student in a circular manner
            presales_team_employees = Employee.objects.filter(department="Presales")

            if presales_team_employees.exists():
                next_index = (last_assigned_index + 1) % presales_team_employees.count()
                enquiry.assign_to_employee = presales_team_employees[next_index]
                enquiry.assign_to_employee.save()

                cache.set("last_assigned_index", next_index)

            # ------------------------------
            enquiry.created_by = user
            enquiry.save()

            create_notification(enquiry.assign_to_employee, "New Enquiry Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=enquiry.assign_to_employee
            ).count()
            try:
                employee_id = enquiry.assign_to_employee.id
                send_notification(employee_id, "New Enquiry Added", current_count)
            except Exception as e:
                pass

            messages.success(request, "Enquiry Added successfully")

            # Clear session data after successful submission
            request.session.pop("enquiry_form1", None)
            request.session.pop("enquiry_form2", None)

            return redirect("enquiry_form4", id=enquiry.id)

        return render(
            request,
            "Admin/Enquiry/lead3.html",
            {"form": form3},
        )

    def get_success_url(self):
        enquiry_id = self.object.id
        return reverse_lazy("enquiry_form4", kwargs={"id": enquiry_id})


# -----------------------------------------------------------


def PackageEnquiry1View(request):
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
        return redirect("packageenquiry_form2")

    context = {"country_choices": country_choices}
    return render(request, "Admin/Enquiry/Package Leads/lead1.html", context)


@login_required
def PackageEnquiry2View(request):
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
        return redirect("packageenquiry_form3")
    return render(request, "Admin/Enquiry/Package Leads/lead2.html")


def PackageEnquiry3View(request):
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
        last_assigned_index = cache.get("last_assigned_index") or 0
        presales_team_employees = Employee.objects.filter(department="Presales")
        if presales_team_employees.exists():
            next_index = (last_assigned_index + 1) % presales_team_employees.count()
            enq.assign_to_employee = presales_team_employees[next_index]
            enq.assign_to_employee.save()

            cache.set("last_assigned_index", next_index)
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
        return redirect("enquiry_form4", enq.id)

    context = {
        "package_id": package_id,
        "package": package,
        "visa_type": visa_type,
        "source": source,
    }
    return render(request, "Admin/Enquiry/Package Leads/lead3.html", context)


# ------------------------------------------


@login_required
def admindocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

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
    }

    return render(request, "Admin/Enquiry/lead4.html", context)


# @login_required
# def upload_document(request):
#     if request.method == "POST":
#         document_id = request.POST.get("document_id")
#         enq_id = request.POST.get("enq_id")

#         document = Document.objects.get(pk=document_id)
#         document_file = request.FILES.get("document_file")
#         enq = Enquiry.objects.get(id=enq_id)
#         # Check if a DocumentFiles object with the same document exists
#         try:
#             doc = DocumentFiles.objects.filter(
#                 enquiry_id=enq_id, document_id=document
#             ).first()
#             if doc:
#                 doc.document_file = document_file
#                 doc.lastupdated_by = request.user
#                 doc.save()

#                 return redirect("enquiry_form4", id=enq_id)
#             else:
#                 documest_files = DocumentFiles.objects.create(
#                     document_file=document_file,
#                     document_id=document,
#                     enquiry_id=enq,
#                     lastupdated_by=request.user,
#                 )
#                 documest_files.save()
#                 return redirect("enquiry_form4", enq_id)

#         except Exception as e:
#             pass


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
        return redirect("enquiry_form4", enq_id)


@login_required
def delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("enquiry_form4", enqq)


# ----------------------------------- Leads Details --------------------------
def get_agent():
    return Agent.objects.all()


def get_outsourcepartner():
    return OutSourcingAgent.objects.all()


@login_required
def admin_new_leads_details(request):
    excluded_statuses = ["Accept", "Case Initiated"]
    lead = [status for status in leads_status if status[0] not in excluded_statuses]
    enquiry = Enquiry.objects.all().order_by("-id")

    presales_employees = get_presale_employee()
    sales_employees = get_sale_employee()
    documentation_employees = get_documentation_team_employee()
    visa_team = get_visa_team_employee()
    assesment_employee = get_assesment_employee()
    agent = get_agent()
    outsourcepartner = get_outsourcepartner()

    context = {
        "enquiry": enquiry,
        "presales_employees": presales_employees,
        "sales_employees": sales_employees,
        "documentation_employees": documentation_employees,
        "visa_team": visa_team,
        "lead": lead,
        "assesment_employee": assesment_employee,
        "agent": agent,
        "outsourcepartner": outsourcepartner
        # "enquiries_with_spouse_names": enquiries_with_spouse_names,
    }
    return render(request, "Admin/Enquiry/lead-details.html", context)


@login_required
def update_assigned_agent(request, id):
    enquiry = Enquiry.objects.get(id=id)
    if request.method == "POST":
        try:
            assign_to_agent = request.POST.get("assign_to_agent")
            agent = Agent.objects.get(id=assign_to_agent)
            enquiry.assign_to_agent = agent

            agent_id = agent.id
            create_notification_agent(agent, "New Lead Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, agent=agent_id
            ).count()
            assign_notification(agent_id, "New Lead Assign Added", current_count)

        except Agent.DoesNotExist:
            if enquiry.assign_to_agent is None:
                enquiry.assign_to_agent = None
            else:
                pass

        enquiry.save()
        return redirect("admin_new_leads_details")
    return render(request, "Admin/Enquiry/lead-details.html")


@login_required
def update_assigned_op(request, id):
    enquiry = Enquiry.objects.get(id=id)
    if request.method == "POST":
        try:
            assign_to_outsourcingagent = request.POST.get("assign_to_outsourcingagent")
           
            outsourcepartner = OutSourcingAgent.objects.get(
                id=assign_to_outsourcingagent
            )
            enquiry.assign_to_outsourcingagent = outsourcepartner

            agent_id = assign_to_outsourcingagent
            create_notification_outsourceagent(
                outsourcepartner, "New Lead Assign Added"
            )

            current_count = Notification.objects.filter(
                is_seen=False, outsourceagent=assign_to_outsourcingagent
            ).count()
            assignop_notification(agent_id, "New Lead Assign Added", current_count)

        except OutSourcingAgent.DoesNotExist:
            if enquiry.assign_to_outsourcingagent is None:
                enquiry.assign_to_outsourcingagent = None
            else:
                pass

        enquiry.save()
        return redirect("admin_new_leads_details")
    return render(request, "Admin/Enquiry/lead-details.html")


@login_required
def update_assigned_employee(request, id):
    enquiry = Enquiry.objects.get(id=id)
    if request.method == "POST":
        ######### ASSIGN CODE #########
        try:
            assign_to_employee = request.POST.get("assign_to_employee")
            emp = Employee.objects.get(id=assign_to_employee)
            enquiry.assign_to_employee = emp
            employee_id = emp.id
            create_notification(emp, "New Lead Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=assign_to_employee
            ).count()
            assign_notification(employee_id, "New Lead Assign Added", current_count)

        except Employee.DoesNotExist:
            if enquiry.assign_to_employee is None:
                enquiry.assign_to_employee = None
            else:
                pass

        try:
            assign_to_assesment_employee = request.POST.get(
                "assign_to_assesment_employee"
            )
            emp = Employee.objects.get(id=assign_to_assesment_employee)
            enquiry.assign_to_assesment_employee = emp

            employee_id = emp.id
            create_notification(emp, "New Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=employee_id
            ).count()
            assign_notification(employee_id, "New Assign Added", current_count)

        except Employee.DoesNotExist:
            if enquiry.assign_to_assesment_employee is None:
                enquiry.assign_to_assesment_employee = None
            else:
                pass

        try:
            assign_to_sales_employee = request.POST.get("assign_to_sales_employee")
            emp = Employee.objects.get(id=assign_to_sales_employee)
            enquiry.assign_to_sales_employee = emp

            employee_id = emp.id
            create_notification(emp, "New Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=employee_id
            ).count()
            assign_notification(employee_id, "New Assign Added", current_count)

        except Employee.DoesNotExist:
            if enquiry.assign_to_sales_employee is None:
                enquiry.assign_to_sales_employee = None
            else:
                pass

        try:
            assign_to_documentation_employee = request.POST.get(
                "assign_to_documentation_employee"
            )
            emp = Employee.objects.get(id=assign_to_documentation_employee)
            enquiry.assign_to_documentation_employee = emp

            employee_id = emp.id
            create_notification(emp, "New Lead Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=employee_id
            ).count()
            assign_notification(employee_id, "New Lead Assign Added", current_count)

        except Employee.DoesNotExist:
            if enquiry.assign_to_documentation_employee is None:
                enquiry.assign_to_documentation_employee = None
            else:
                pass

        try:
            assign_to_visa_team_employee = request.POST.get(
                "assign_to_visa_team_employee"
            )
            emp = Employee.objects.get(id=assign_to_visa_team_employee)
            enquiry.assign_to_visa_team_employee = emp

            employee_id = emp.id
            create_notification(emp, "New Assign Added")

            current_count = Notification.objects.filter(
                is_seen=False, employee=employee_id
            ).count()
            assign_notification(employee_id, "New Assign Added", current_count)

        except Employee.DoesNotExist:
            if enquiry.assign_to_visa_team_employee is None:
                enquiry.assign_to_visa_team_employee = None
            else:
                pass
        enquiry.save()
        return redirect("admin_new_leads_details")
    return render(request, "Admin/Enquiry/lead-details.html")


@login_required
def admin_grid_leads_details(request):
    enquiry = Enquiry.objects.all().order_by("-id")

    context = {"enquiry": enquiry}
    return render(request, "Admin/Enquiry/lead-grid.html", context)


def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        data = response.json()
        return data["ip"]
    except Exception as e:
        # Handle the exception (e.g., log the error)
        return None


def add_notes(request):
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

    return redirect("admin_new_leads_details")


############################################### CHANGE PASSWORD ###########################################


@login_required
def ChangePassword(request):
    user = request.user
    admin = Admin.objects.get(users=user)

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

    return render(request, "Admin/Dashboard/dashboard.html")


############################################ ARCHIVE LEADS ###############################################


@login_required
def delete_and_archive(request, id):
    instance = get_object_or_404(Enquiry, id=id)

    instance.archive = True
    instance.save()

    return redirect("admin_new_leads_details")


@login_required
def restore(request, id):
    instance = get_object_or_404(Enquiry, id=id)

    instance.archive = False
    instance.save()

    return redirect("Archive_list")


class ArchiveListView(LoginRequiredMixin, ListView):
    template_name = "Admin/Enquiry/archivelist.html"
    context_object_name = "enquiries"

    def get_queryset(self):
        return Enquiry.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context["current_datetime"] = current_datetime

        context["notes"] = Notes.objects.all()
        context["employee_queryset"] = Employee.objects.all()

        return context


############################################## ENROLLED LEADS ##############################################


class enrolled_Application(LoginRequiredMixin, ListView):
    model = Enquiry
    template_name = "Admin/Enquiry/Enrolled Enquiry/Enrolledleads.html"
    context_object_name = "enquiry"

    def get_queryset(self):
        return Enquiry.objects.filter(
            Q(lead_status="Enrolled")
            | Q(lead_status="Inprocess")
            | Q(lead_status="Ready To Submit")
            | Q(lead_status="Appointment")
            | Q(lead_status="Ready To Collection")
            | Q(lead_status="Result")
            | Q(lead_status="Delivery")
        ).order_by("-id")

    def get_context_data(self, **kwargs):
        # Get the default context data (data from the Enquiry model)
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context["current_datetime"] = current_datetime

        # Add data from the Notes model to the context
        context["notes"] = Notes.objects.all()
        context["notes_first"] = Notes.objects.order_by("-id").first()
        # context['employee'] = Employee.objects.all()
        context["employee_queryset"] = Employee.objects.all()
        context["agent"] = Agent.objects.all()
        context["OutSourcingAgent"] = OutSourcingAgent.objects.all()
        context["enqenrolled"] = Enquiry.objects.filter(lead_status="Enrolled")

        return context


class enrolledGrid_Application(LoginRequiredMixin, ListView):
    model = Enquiry
    template_name = "Admin/Enquiry/enroll_lead-grid.html"
    context_object_name = "enquiry"

    def get_queryset(self):
        return Enquiry.objects.filter(
            Q(lead_status="Enrolled")
            | Q(lead_status="Inprocess")
            | Q(lead_status="Ready To Submit")
            | Q(lead_status="Appointment")
            | Q(lead_status="Ready To Collection")
            | Q(lead_status="Result")
            | Q(lead_status="Delivery")
        ).order_by("-id")

    def get_context_data(self, **kwargs):
        # Get the default context data (data from the Enquiry model)
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context["current_datetime"] = current_datetime

        # Add data from the Notes model to the context
        context["notes"] = Notes.objects.all()
        context["notes_first"] = Notes.objects.order_by("-id").first()
        # context['employee'] = Employee.objects.all()
        context["employee_queryset"] = Employee.objects.all()
        context["agent"] = Agent.objects.all()
        context["OutSourcingAgent"] = OutSourcingAgent.objects.all()
        context["enqenrolled"] = Enquiry.objects.filter(lead_status="Enrolled")

        return context


######################################### EMPLOYEE FILTER ##################################################


def get_sale_employee():
    return Employee.objects.filter(department="Sales")


def get_presale_employee():
    return Employee.objects.filter(department="Presales")


def get_assesment_employee():
    return Employee.objects.filter(department="Assesment")


def get_documentation_team_employee():
    return Employee.objects.filter(department="Documentation")


def get_visa_team_employee():
    return Employee.objects.filter(department="Visa Team")


@login_required
def edit_enrolled_application(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()

    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
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

        return redirect("education_summary", id=id)

    return render(
        request,
        "Admin/Enquiry/Enrolled Enquiry/Editenrolledpart1.html",
        context,
    )


@login_required
def combined_view(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    education_summary = Education_Summary.objects.filter(enquiry_id=enquiry).first
    work_exp = Work_Experience.objects.filter(enquiry_id=enquiry).first
    bk_info = Background_Information.objects.filter(enquiry_id=enquiry).first

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

        return redirect("edit_product_details", id=id)

    test_scores = TestScore.objects.filter(enquiry_id=enquiry)

    context = {
        "enquiry": enquiry,
        "test_scores": test_scores,
        "education_summary": education_summary,
        "work_exp": work_exp,
        "bk_info": bk_info,
    }

    return render(
        request, "Admin/Enquiry/Enrolled Enquiry/Editenrolledpart2.html", context
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
    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "product": product,
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

        return redirect("enrolled_document", id=id)

    return render(
        request,
        "Admin/Enquiry/Enrolled Enquiry/Editenrolledpart3.html",
        context,
    )


@login_required
def enrolleddocument(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

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
    }

    return render(
        request, "Admin/Enquiry/Enrolled Enquiry/Editenrolledpart4.html", context
    )


@login_required
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
        return redirect("enrolled_document", id=enq_id)


@login_required
def enrolled_delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect("enrolled_document", enqq)


############################################### LOGOUT #####################################################


@login_required
def admin_logout(request):
    logout(request)
    return redirect("/")


########################################### ACTIVITY LOGS ################################################


@login_required
def activity_log_view(request):
    activity_logs = ActivityLog.objects.all().order_by("-id")

    context = {"activity_logs": activity_logs}

    return render(request, "Admin/ActivityLogs/Activitylogs.html", context)


########################################## FAQ ####################################################


def get_pending_queries_count():
    return FAQ.objects.filter(answer__exact="").exclude(answer__isnull=True).count()


class ResolvedFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Admin/Queries/Queries.html"
    context_object_name = "resolved_queries"

    def get_queryset(self):
        return FAQ.objects.all().exclude(answer="")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_queries_count"] = get_pending_queries_count()
        return context


class PendingFAQListView(LoginRequiredMixin, ListView):
    model = FAQ
    template_name = "Admin/Queries/PendingQueries.html"
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
        return HttpResponseRedirect(reverse("Admin_resolved_queries"))


class FAQCreateView(LoginRequiredMixin, CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = "Admin/Queries/add_query.html"
    success_url = reverse_lazy("Admin_pending_queries")

    def form_valid(self, form):
        instance = form.save(commit=False)

        instance.user = self.request.user
        instance.save()
        messages.success(self.request, "FAQ Added Successfully.")

        return super().form_valid(form)


@login_required
def delete_query(request, id):
    query = FAQ.objects.get(id=id)
    query.delete()
    messages.success(request, "Query deleted successfully..")
    return HttpResponseRedirect(reverse("Admin_resolved_queries"))


class profileview(TemplateView, LoginRequiredMixin):
    template_name = "Admin/Profile/Profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        context["user"] = user

        if hasattr(user, "get_user_type_display"):
            context["user_type"] = user.get_user_type_display()

        return context


@login_required
def edit_profile(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        contact = request.POST.get("contact")

        admin_instance = Admin.objects.get(users=request.user)

        admin_instance.users.first_name = first_name
        admin_instance.users.last_name = last_name
        admin_instance.users.email = email
        admin_instance.contact_no = contact

        admin_instance.users.save()
        admin_instance.save()

        return redirect("admin_profile")

    return render(request, "Admin/Profile/Profile.html")


def leadupated(request, id):
    enquiry = Enquiry.objects.get(id=id)
    if request.method == "POST":
        lead = request.POST.get("lead")

        if lead == "New Lead":
            enquiry.lead_status = "Active"  # sales
            enquiry.save()
        if lead == "Active":
            enquiry.lead_status = "PreEnrolled"  # sales
            enquiry.save()
        elif lead == "PreEnrolled":
            enquiry.lead_status = "Enrolled"  # visa team
            enquiry.save()
        elif lead == "Enrolled":
            enquiry.lead_status = "Inprocess"  # Documentation team
            enquiry.save()
        elif lead == "Inprocess":
            enquiry.lead_status = "Ready To Submit"  # Documentation team
            enquiry.save()
        elif lead == "Ready To Submit":
            enquiry.lead_status = "Appointment"  # Documentation team
            enquiry.save()
        elif lead == "Appointment":
            enquiry.lead_status = "Ready To Collection"  # Documentation team
            enquiry.save()
        elif lead == "Ready To Collection":
            enquiry.lead_status = "Result"  # Documentation team
            enquiry.save()
        elif lead == "Result":
            enquiry.lead_status = "Delivery"  # Documentation team
            enquiry.save()

    return redirect("admin_new_leads_details")


# ------------------------------------ GROUP CHAT --------------------


class CreateChatGroupView(LoginRequiredMixin, CreateView):
    model = ChatGroup
    form_class = ChatGroupForm
    template_name = "chat/chatgroup.html"
    success_url = reverse_lazy("ChatGroup_list")

    def form_valid(self, form):
        chat_group = form.save(commit=False)

        chat_group.create_by = self.request.user

        chat_group.save()

        chat_group.group_member.add(self.request.user)

        messages.success(self.request, "ChatGroup Added Successfully.")
        return super().form_valid(form)


class ChatGroupListView(LoginRequiredMixin, ListView):
    model = ChatGroup
    template_name = "chat/grouplist.html"
    context_object_name = "group"

    def get_queryset(self):
        return ChatGroup.objects.order_by("-id")


class editGroupChat(LoginRequiredMixin, UpdateView):
    model = ChatGroup
    form_class = ChatGroupForm
    template_name = "chat/updategroup.html"
    success_url = reverse_lazy("ChatGroup_list")

    def form_valid(self, form):
        form.instance.lastupdated_by = self.request.user

        messages.success(self.request, "ChatGroup Updated Successfully.")

        return super().form_valid(form)


def chat_group_delete_group(request, id):
    group = get_object_or_404(ChatGroup, id=id)
    group.delete()
    messages.success(request, f"{group.group_name} deleted successfully..")
    return redirect("ChatGroup_list")


# ----------------------------- Lead Updated ---------------------------


def admin_lead_updated(request, id):
    if request.method == "POST":
        lead_status = request.POST.get("lead_status")
        enquiry = Enquiry.objects.get(id=id)
        enquiry.lead_status = lead_status
        enquiry.save()
        messages.success(request, f"Lead {lead_status} Status Updated Successfully...")
        return HttpResponseRedirect(reverse("admin_new_leads_details"))


########################################## LEAD APPOINTMENT ########################################


def admin_appointment_Save(request):
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

        return redirect("admin_new_leads_details")


def admin_appointment_done(request, id):
    enq = Enquiry.objects.get(id=id)

    enq_appointment = EnqAppointment.objects.get(enquiry=enq)
    enq_appointment.status = "Done"

    enq_appointment.save()
    return redirect("admin_new_leads_details")


@login_required
def approve_product(request, id):
    instance = get_object_or_404(Package, id=id)

    instance.approval = True
    instance.save()

    send_whatsapp_messages(instance)
    send_email(instance)

    return redirect("Package_list")


def send_email(package_instance):
    title = package_instance.title if package_instance.title else None
    country = (
        package_instance.visa_country.country
        if (package_instance.visa_country)
        else None
    )

    send_package_email(title, country)


def send_whatsapp_messages(package_instance):
    user_types = ["2", "3", "4", "5", "6"]
    for user_type in user_types:
        users = CustomUser.objects.filter(user_type=user_type)
        for user in users:
            contact = get_contact_number(user)
            if contact:
                title = package_instance.title if package_instance.title else None
                country = (
                    package_instance.visa_country.country
                    if (package_instance.visa_country)
                    else None
                )
                message = (
                    f"🌟 Greetings User! 🌟 \n\n"
                    f" *We are thrilled to share with you our latest addition to our visa services: * \n\n"
                    f" {title} for {country}.  \n\n"
                    f" This is a great opportunity for you to work in one of the most beautiful and diverse countries in the world. \n\n"
                )
                response = send_whatsapp_message(contact, message)
                if response.status_code == 200:
                    pass
                else:
                    pass


def get_contact_number(user):
    # Method to get the contact number based on user type
    if user.user_type == "2":
        return Admin.objects.get(users=user).contact_no
    elif user.user_type == "3":
        return Employee.objects.get(users=user).contact_no
    elif user.user_type == "4":
        return Agent.objects.get(users=user).contact_no
    elif user.user_type == "5":
        return OutSourcingAgent.objects.get(users=user).contact_no

    return None


@login_required
def disapprove_product(request, id):
    instance = get_object_or_404(Package, id=id)

    instance.approval = False
    instance.save()

    return redirect("Package_list")


########################################## SUCCESSSTORY ##################################################


@login_required
def add_successstory(request):
    successstory = SuccessStory.objects.all().order_by("-id")
    form = SuccessStoryForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        user = request.user
        form.instance.create_by = user
        form.save()
        messages.success(request, "Success Story added successfully")
        return HttpResponseRedirect(reverse("Successstory_list"))

    context = {"form": form, "story": successstory}
    return render(request, "Admin/SuccessStory/successstorylist.html", context)


@login_required
def delete_successstory(request, id):
    successstory_id = SuccessStory.objects.get(id=id)
    successstory_id.delete()
    messages.success(request, "Success Story deleted successfully..")
    return HttpResponseRedirect(reverse("Successstory_list"))


############################################# NEWS #####################################################


@login_required
def add_news(request):
    news = News.objects.all().order_by("-id")
    form = NewsForm(request.POST or None)

    if form.is_valid():
        user = request.user
        form.instance.create_by = user
        form.save()
        messages.success(request, "News added successfully")
        return HttpResponseRedirect(reverse("News_list"))

    context = {"form": form, "news": news}
    return render(request, "Admin/News/newslist.html", context)


@login_required
def delete_news(request, id):
    news_id = News.objects.get(id=id)
    news_id.delete()
    messages.success(request, "News deleted successfully..")
    return HttpResponseRedirect(reverse("News_list"))


def switch_to_outsource_agent(request, agent_id):
    try:
        agent = Agent.objects.get(id=agent_id)

        custom_user = agent.users
        # Update user_type to OutSourcing Agent
        custom_user.user_type = (
            "5"  # Update to the appropriate value for OutSourcing Agent
        )

        # Create an OutSourcingAgent instance with the same data as Agent
        outsource_agent = OutSourcingAgent.objects.create(
            users=custom_user,
            type="Outsourcing Partner",
            contact_no=agent.contact_no,
            country=agent.country,
            state=agent.state,
            City=agent.City,
            Address=agent.Address,
            zipcode=agent.zipcode,
            dob=agent.dob,
            marital_status=agent.marital_status,
            status=agent.status,
            activeinactive=agent.activeinactive,
            profile_pic=agent.profile_pic,
            assign_employee=agent.assign_employee,
            organization_name=agent.organization_name,
            business_type=agent.business_type,
            registration_number=agent.registration_number,
            account_holder=agent.account_holder,
            bank_name=agent.bank_name,
            branch_name=agent.branch_name,
            account_no=agent.account_no,
            ifsc_code=agent.ifsc_code,
            last_updated=agent.last_updated,
            registeron=agent.registeron,
            registerdby=custom_user,
            # Copy other fields as needed
        )
        if agent.gender:
            outsource_agent.gender = (agent.gender,)

        custom_user.save()

        agent_agreements = AgentAgreement.objects.filter(agent=agent)
        for agreement in agent_agreements:
            agreement.outsourceagent = OutSourcingAgent.objects.get(users=custom_user)
            agreement.agent = None
            agreement.save()

        enquiries_assigned_to_agent = Enquiry.objects.filter(assign_to_agent=agent)

        for enquiry in enquiries_assigned_to_agent:
            enquiry.assign_to_outsourcingagent = custom_user.outsourcingagent
            enquiry.assign_to_agent = None

            enquiry.save()
        try:
            agent_kyc = AgentKyc.objects.get(agent=agent)

            agent_kyc.outsourceagent = OutSourcingAgent.objects.get(users=custom_user)
            agent_kyc.agent = None
            agent_kyc.save()
        except AgentKyc.DoesNotExist:
            # Handle the case when no AgentKyc record is found
            # You can create a new AgentKyc record or perform any other desired action
            agent_kyc = AgentKyc.objects.create(
                agent=agent,
                outsourceagent=OutSourcingAgent.objects.get(users=custom_user),
                # Set other fields as needed
            )
            # Optionally, you can log the error or display a message

            # Handle any additional logic or related models here

            messages.success(request, "Agent switched to Outsource Agent successfully.")
        agent.delete()
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found.")

    return redirect("agent_list")


class ReportList(LoginRequiredMixin, ListView):
    model = Report
    template_name = "Admin/Report/report.html"
    context_object_name = "report"

    def get_queryset(self):
        return Report.objects.order_by("-id")


import pdfkit


def email_template(request):
    context = {"hello": "hello"}
    # return render(request, "email_template.html")
    return PDFTemplateResponse(request, "email_template.html", context)
    # pdfkit.from_file("email_template.html", "file.pdf")


def color_code(request, id):
    if request.method == "POST":
        color_code = request.POST.get("color_code")
        enquiry = Enquiry.objects.get(id=id)
        enquiry.color_code = color_code
        enquiry.save()
        messages.success(request, f"Lead Color {color_code} Updated Successfully...")
        return HttpResponseRedirect(reverse("admin_new_leads_details"))


def admin_appointment(request):
    all_events = Appointment.objects.all()

    context = {"events": all_events}
    return render(request, "Admin/Dashboard/demo.html", context)


def NewsUpdateView(request):
    user = request.user

    if request.method == "POST":
        news_id = request.POST.get("news_id")
        news_text = request.POST.get("news")
        employee = request.POST.get("employee")  # This might be "on" or None
        agent = request.POST.get("agent")
        outsource_Agent = request.POST.get("outsource_Agent")

        # Fetch the News object by ID
        news_instance = News.objects.get(id=news_id)

        # Update the fields
        news_instance.news = news_text
        news_instance.agent = agent
        news_instance.outsource_Agent = outsource_Agent

        news_instance.employee = True if employee == "on" else False
        news_instance.agent = True if agent == "on" else False
        news_instance.outsource_Agent = True if outsource_Agent == "on" else False

        news_instance.create_by = user

        # Save the changes
        news_instance.save()

        messages.success(request, "News Updated successfully")
        return HttpResponseRedirect(reverse("News_list"))


def add_appointment(request):
    start = request.GET.get("start", None)
    end = request.GET.get("time", None)
    time = request.GET.get("time", None)
    
    title = request.GET.get("title", None)
    event = Appointment(name=str(title), start=start, time=time)
    event.save()
    data = {}
    return JsonResponse(data)


# def all_appointment(request):
#     try:
#         all_appointment = Appointment.objects.all()
#         out = []
#         for appointment in all_appointment:
#             formatted_start = appointment.start.astimezone(
#                 timezone.get_current_timezone()
#             ).strftime("%Y-%m-%dT%H:%M:%S")
#             formatted_end = appointment.start.astimezone(
#                 timezone.get_current_timezone()
#             ).strftime("%Y-%m-%dT%H:%M:%S")
#             out.append(
#                 {
#                     "title": appointment.name,
#                     "id": appointment.id,
#                     "start": formatted_start,
#                     "end": formatted_end,
#                 }
#             )
#         return JsonResponse(out, safe=False)
#     except Exception as e:
#         print(
#             f"Error in all_events view: {str(e)}"
#         )  # Print the error message to the console
#         return JsonResponse({"error": "Internal Server Error"}, status=500)

from django.core.serializers.json import DjangoJSONEncoder


def all_appointment(request):
    all_events = Appointment.objects.all()
    
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


def update(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)
    id = request.GET.get("id", None)
    print("ssssssssssssss", id)
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


def add_todo(request):
    description = request.POST.get("todoDescription")

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        task = Todo.objects.create(user=request.user, description=description)

        return HttpResponseRedirect(reverse("admin_dashboard"))
    except Exception as e:
        pass


def update_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields
        description = request.POST.get("todoDescription")

        todo.description = description
        todo.save()

        return HttpResponseRedirect(reverse("admin_dashboard"))
    except Exception as e:
        pass


def delete_todo(request, id):
    todo = Todo.objects.get(id=id)

    try:
        # Assuming you have a Task model with 'title' and 'description' fields

        todo.delete()

        return HttpResponseRedirect(reverse("admin_dashboard"))
    except Exception as e:
        pass


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


######################################## FILTER SEARCH ##################################################


@login_required
def search_enquiries(request):
    enquiry = Enquiry.objects.all().order_by("-id")

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
            enquiry = enquiry.filter(filter_conditions)

    return render(request, "Admin/Enquiry/lead-details.html", {"enquiry": enquiry})


@login_required
def search_employee(request):
    employee = Employee.objects.all().order_by("-id")

    if request.method == "POST":
        emp_code = request.POST.get("emp_code")
        name = request.POST.get("name")
        email = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        branch = request.POST.get("branch")
        department = request.POST.get("department")

        filter_conditions = Q()

        if emp_code:
            filter_conditions &= Q(emp_code__icontains=emp_code)

        if name:
            names = name.split()

            first_name_condition = Q()
            last_name_condition = Q()

            for n in names:
                first_name_condition |= Q(users__first_name__icontains=n)
                last_name_condition |= Q(users__last_name__icontains=n)

            filter_conditions &= first_name_condition & last_name_condition

        if email:
            filter_conditions &= Q(users__email__icontains=email)

        if contact_no:
            filter_conditions &= Q(contact_no__icontains=contact_no)

        if branch:
            filter_conditions &= Q(branch__branch_name__icontains=branch)

        if department and department != "Select":
            filter_conditions &= Q(department=department)

        if filter_conditions:
            employee = employee.filter(filter_conditions)

    return render(
        request, "Admin/Employee Management/Employeelist.html", {"employee": employee}
    )


############################################### VISA TEAM COLOUR ##########################################


@login_required
def visa_team_color(request):
    if request.method == "POST":
        selected_user_ids = request.POST.getlist("selected_users")
        color_code = request.POST.get("color_code")

        for user_id in selected_user_ids:
            employee = get_object_or_404(Employee, users__id=user_id)
            employee.color_code = color_code
            employee.save()

        messages.success(request, "Colour Added successfully")
        return redirect("color_employee_list")

    visateam = get_visa_team_employee()
    context = {"visateam": visateam}
    return render(request, "Admin/Employee Management/add_color_team.html", context)


@login_required
def color_employee_list(request):
    employees = Employee.objects.filter(department="Visa Team")
    return render(
        request,
        "Admin/Employee Management/visateam_colorlist.html",
        {"employees": employees},
    )


@login_required
def visateamcolorupdate_view(request):
    if request.method == "POST":
        users = request.POST.get("users_id")
        color_code = request.POST.get("color_code")

        users_id = Employee.objects.get(id=users)
        users_id.color_code = color_code

        users_id.save()
        messages.success(request, "Team Updated successfully")
        return HttpResponseRedirect(reverse("color_employee_list"))
