from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django_countries.fields import CountryField
from django.core.cache import cache
from django.db.models import Count
import datetime
from django.db.models import Q
import json


BRANCH_SOURCES = [
    ("COCO", "Company Owned Company Operated"),
    ("COFO", "Company Owned Franchise Operated"),
    ("FOCO", "Franchise Owned Company Operated"),
    ("FOFO", "Franchise Owned Franchise Operated"),
]

COURIER_STATUS = [
    ("Pick", "Pick"),
    ("In Transit", "In Transit"),
    ("Receive", "Receive"),
]

type = [
    ("Outsourcing partner", "Outsourcing partner"),
    ("Agent", "Agent"),
]

status = [
    ("Pending", "Pending"),
    ("InReview", "InReview"),
    ("Approved", "Approved"),
    ("Reject", "Reject"),
]

Department_Choices = [
    ("Presales", "Presales"),
    ("Assesment", "Assesment"),
    ("Sales", "Sales"),
    ("Documentation", "Documentation"),
    ("Visa Team", "Visa Team"),
    ("HR", "HR"),
    ("Developement Team", "Developement Team"),
    ("Design Team", "Design Team"),
    ("Account Team", "Account Team"),
]

PRIORITY_CHOICES = (
    ("High", "High"),
    ("Medium", "Medium"),
    ("Low", "Low"),
)

FOLLOWUP_STATUS_CHOICES = (("Inprocess", "Inprocess"), ("Done", "Done"))


TYPE_CHOICES = [("Appointment", "Appointment"), ("Contact Us", "Contact Us")]


class CustomUser(AbstractUser):
    user_type_data = (
        ("1", "HOD"),
        ("2", "Admin"),
        ("3", "Employee"),
        ("4", "Agent"),
        ("5", "Out Sourcing Agent"),
        ("6", "Customer"),
    )
    user_type = models.CharField(default="1", choices=user_type_data, max_length=10)
    is_logged_in = models.BooleanField(default=False)

    def generate_initials(self):
        first_initial = self.first_name[0].upper() if self.first_name else ""
        last_initial = self.last_name[0].upper() if self.last_name else ""
        return f"{first_initial}{last_initial}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Admin(models.Model):
    users = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.users.first_name


class VisaCountry(models.Model):
    country = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now=True)
    lastupdated_by = models.CharField(max_length=100, null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.country)

    # class Meta:
    #     db_table = "VisaCountry"


class VisaCategory(models.Model):
    visa_country_id = models.ForeignKey(VisaCountry, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100)
    lastupdated_by = models.CharField(max_length=100, null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "VisaCategory"

    def __str__(self):
        return f"{self.category} - {self.subcategory}"


class DocumentCategory(models.Model):
    Document_category = models.CharField(max_length=200)
    lastupdated_by = models.CharField(max_length=100, null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.Document_category


class Document(models.Model):
    document_name = models.CharField(max_length=255)
    document_category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE)

    lastupdated_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.document_name


class CaseCategoryDocument(models.Model):
    country = models.OneToOneField(VisaCountry, on_delete=models.CASCADE)
    category = models.ForeignKey(
        VisaCategory, on_delete=models.CASCADE, related_name="case_category"
    )
    # subcategory = models.ForeignKey(VisaCategory,on_delete=models.CASCADE,related_name='case_subcategory')
    document = models.ManyToManyField(Document, related_name="document")
    last_updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.country} - {self.category}"


class Branch(models.Model):
    branch_name = models.CharField(max_length=20)
    branch_source = models.CharField(max_length=50, choices=BRANCH_SOURCES)
    last_updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.branch_name


class Group(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    group_member = models.ManyToManyField(CustomUser, related_name="groups_member")
    create_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group_name


class CourierAddress(models.Model):
    company_name = models.CharField(max_length=200)
    address = models.CharField(max_length=200, blank=True, null=True)
    landmark = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)
    zipcode = models.IntegerField()
    docker_no = models.CharField(max_length=100)
    sender_no = models.CharField(max_length=15, blank=True, null=True)
    receiver_no = models.CharField(max_length=15, blank=True, null=True)
    courier_no = models.CharField(max_length=15, blank=True, null=True)
    receiver_address = models.CharField(max_length=150)
    sender_address = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, choices=COURIER_STATUS)
    lastupdated_by = models.CharField(max_length=100, null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True)


class LoginLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    platform = models.CharField(max_length=200, default="Web")
    ip_address = models.GenericIPAddressField()
    login_datetime = models.DateTimeField(auto_now_add=True)
    # date = models.DateField()

    def save(self, *args, **kwargs):
        # Format the date and time as "13-Sep-2023 01:56 PM"
        formatted_datetime = self.login_datetime.strftime("%d-%b-%Y %I:%M %p")
        self.login_datetime_formatted = formatted_datetime
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.login_datetime}"


COLOR_CODE = [
    ("Grey", "Grey"),
    ("Blue", "Blue"),
    ("White", "White"),
    ("Red", "Red"),
    ("Green", "Green"),
]


class Employee(models.Model):
    users = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    emp_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(
        max_length=20, null=True, blank=True, choices=Department_Choices
    )
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    contact_no = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    City = models.CharField(max_length=50, null=True, blank=True)
    Address = models.TextField(null=True, blank=True)
    zipcode = models.CharField(max_length=100, null=True, blank=True)
    file = models.FileField(
        upload_to="media/Employee/profile_pic/", null=True, blank=True
    )
    created = models.DateTimeField(auto_now=True)
    tata_tele_authorization = models.CharField(max_length=500, null=True, blank=True)
    tata_tele_api_key = models.CharField(max_length=200, null=True, blank=True)
    tata_tele_agent_number = models.CharField(max_length=200, null=True, blank=True)
    color_code = models.CharField(
        max_length=20, choices=COLOR_CODE, blank=True, null=True
    )

    def save(self, *args, **kwargs):
        # Check if a group is provided when saving the employee
        if self.group:
            # Add the employee to the group
            self.group.group_member.add(self.users)
        super(Employee, self).save(*args, **kwargs)

    def __str__(self):
        return self.users.username


marital_status = [
    ("Single", "Single"),
    ("Married", "Married"),
]

Gender = [
    ("Male", "Male"),
    ("Female", "Female"),
]


class Agent(models.Model):
    users = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    City = models.CharField(max_length=50)
    Address = models.TextField()
    zipcode = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender, null=True, blank=True)
    marital_status = models.CharField(
        max_length=50, choices=marital_status, null=True, blank=True
    )
    status = models.CharField(max_length=255, choices=status, default="Pending")
    activeinactive = models.BooleanField(default=True, null=True, blank=True)
    profile_pic = models.ImageField(
        upload_to="media/Agent/Profile Pic/", null=True, blank=True
    )
    assign_employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )

    organization_name = models.CharField(max_length=100, null=True, blank=True)
    business_type = models.CharField(max_length=100, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)

    # ---------- Bank Information ----------------

    account_holder = models.CharField(max_length=100, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=100, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    registeron = models.DateTimeField(auto_now_add=True, auto_now=False)
    registerdby = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_agents",
    )

    # -------------------------- kyc information ------------------

    adhar_card_front = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    adhar_card_back = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    pancard = models.FileField(upload_to="media/Agent/Kyc", null=True, blank=True)
    registration_certificate = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )

    def __str__(self):
        return f"{self.users.first_name} {self.users.last_name}"


class OutSourcingAgent(models.Model):
    users = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    City = models.CharField(max_length=50)
    Address = models.TextField()
    zipcode = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    marital_status = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=255, choices=status, default="Pending")
    activeinactive = models.BooleanField(default=True, null=True, blank=True)
    profile_pic = models.ImageField(
        upload_to="media/OutSourcing/Agent/Profile Pic/", null=True, blank=True
    )
    assign_employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )

    organization_name = models.CharField(max_length=100, null=True, blank=True)
    business_type = models.CharField(max_length=100, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)

    # ---------- Bank Information ----------------

    account_holder = models.CharField(max_length=100, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=100, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    registeron = models.DateTimeField(auto_now_add=True, auto_now=False)
    registerdby = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_outsourcingagents",
    )

    # -------------------------- kyc information ------------------

    adhar_card_front = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    adhar_card_back = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    pancard = models.FileField(upload_to="media/Agent/Kyc", null=True, blank=True)
    registration_certificate = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )

    def _str_(self):
        return f"{self.users.first_name} {self.users.last_name}"


PROCESSING_TIME_CHOICES = [
    ("1 Month", "1 Month"),
    ("2 Month", "2 Month"),
    ("3 Month", "3 Month"),
    ("4 Month", "4 Month"),
    ("5 Month", "5 Month"),
    ("6 Month", "6 Month"),
]


class Package(models.Model):
    visa_country = models.ForeignKey(
        VisaCountry, on_delete=models.SET_NULL, null=True, blank=True
    )
    visa_category = models.ForeignKey(
        VisaCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_category",
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    assign_to_group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True
    )
    number_of_visa = models.IntegerField(null=True, blank=True)
    amount = models.CharField(max_length=100, null=True, blank=True)
    advance_amount = models.CharField(max_length=100, null=True, blank=True)
    file_charges = models.CharField(max_length=100, null=True, blank=True)
    package_expiry_date = models.DateField(auto_created=False, null=True, blank=True)
    last_updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True)
    image = models.FileField(upload_to="media/package_images/", null=True, blank=True)
    processing_time = models.CharField(
        max_length=30, choices=PROCESSING_TIME_CHOICES, blank=True, null=True
    )
    approval = models.BooleanField(default="False")

    def __str__(self):
        return self.title


class VisaSubcategory(models.Model):
    country_id = models.ForeignKey(VisaCountry, on_delete=models.CASCADE)
    category_id = models.ForeignKey(
        VisaCategory, on_delete=models.CASCADE, related_name="pricing_category"
    )
    subcategory_name = models.ForeignKey(
        VisaCategory, on_delete=models.CASCADE, related_name="pricing_subcategory"
    )
    # person = models.ManyToManyField(CustomUser)
    estimate_amt = models.FloatField()
    cgst = models.FloatField()
    sgst = models.FloatField()
    totalAmount = models.FloatField()
    lastupdated_by = models.CharField(max_length=100, null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Pricing"

    def __str__(self):
        return f"{self.country_id} - {self.category_id} - {self.subcategory_name}"


class AgentAgreement(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    outsourceagent = models.ForeignKey(
        OutSourcingAgent, on_delete=models.SET_NULL, null=True, blank=True
    )
    agreement_name = models.CharField(max_length=100)
    agreement_file = models.FileField(
        upload_to="media/Agreement/", null=True, blank=True
    )


class AgentKyc(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    outsourceagent = models.ForeignKey(
        OutSourcingAgent, on_delete=models.SET_NULL, null=True, blank=True
    )
    adhar_card_front = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    adhar_card_back = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    pancard = models.FileField(upload_to="media/Agent/Kyc", null=True, blank=True)
    registration_certificate = models.FileField(
        upload_to="media/Agent/Kyc", null=True, blank=True
    )
    uploaded_on = models.DateTimeField(auto_now=True)


class Booking(models.Model):
    email = models.EmailField()
    fullname = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    departure_city = models.CharField(max_length=100)
    number_of_people = models.PositiveIntegerField()
    departure_date = models.DateField()


SALUTATION_CHOICES = [
    ("Mr", "Mr"),
    ("Mrs", "Mrs"),
    ("Miss", "Miss"),
    ("Master", "Master"),
]


VISATYPE_CHOICES = [("Single", "Single"), ("Couple", "Couple"), ("Family", "Family")]
source = [
    ("Facebook", "Facebook"),
    ("Instagram", "Instagram"),
    ("Twitter", "Twitter"),
    ("Reference", "Reference"),
    ("Youtube", "Youtube"),
    ("WhatsApp", "WhatsApp"),
    ("Google", "Google"),
    ("Others", "Others"),
]


leads_status = [
    ("New Lead", "New Lead"),
    ("Accept", "Accept"),
    ("Active", "Active"),
    ("PreEnrolled", "PreEnrolled"),
    ("Enrolled", "Enrolled"),
    ("Inprocess", "Inprocess"),
    ("Ready To Submit", "Ready To Submit"),
    ("Appointment", "Appointment"),
    ("Ready To Collection", "Ready To Collection"),
    ("Result", "Result"),
    ("Delivery", "Delivery"),
    ("Reject", "Reject"),
    ("Case Initiated", "Case Initiated"),
]


class Enquiry(models.Model):
    Salutation = models.CharField(
        max_length=20, choices=SALUTATION_CHOICES, null=True, blank=True
    )
    FirstName = models.CharField(max_length=50, null=True, blank=True, default="")
    MiddleName = models.CharField(max_length=50, null=True, blank=True, default="")
    LastName = models.CharField(max_length=50, null=True, blank=True, default="")
    Dob = models.DateField(null=True, blank=True)
    Gender = models.CharField(max_length=10, choices=Gender, null=True, blank=True)
    marital_status = models.CharField(max_length=100, null=True, blank=True)

    Visa_country = models.ForeignKey(
        VisaCountry, on_delete=models.SET_NULL, null=True, blank=True
    )
    Visa_category = models.ForeignKey(
        VisaCategory,
        on_delete=models.CASCADE,
        related_name="enquiry_category",
        null=True,
        blank=True,
    )
    Visa_subcategory = models.ForeignKey(
        VisaCategory,
        on_delete=models.CASCADE,
        related_name="enquiry_subcategory",
        null=True,
        blank=True,
    )

    Visa_type = models.CharField(
        max_length=50, choices=VISATYPE_CHOICES, null=True, blank=True
    )
    Package = models.ForeignKey(
        Package, on_delete=models.CASCADE, null=True, blank=True
    )
    Source = models.CharField(max_length=100, choices=source, null=True, blank=True)
    Reference = models.CharField(max_length=100, null=True, blank=True)
    lead_status = models.CharField(
        max_length=100, choices=leads_status, default="New Lead"
    )
    # manage_status = models.CharField(max_length=100,choices=manage_status,default="Pending")
    enquiry_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    assign_to_employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    assign_to_assesment_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assesment_emp",
    )
    assign_to_sales_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_emp",
    )

    assign_to_documentation_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentation_emp",
    )
    assign_to_visa_team_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visa_team_emp",
    )
    assign_to_agent = models.ForeignKey(
        Agent, on_delete=models.SET_NULL, null=True, blank=True
    )
    assign_to_outsourcingagent = models.ForeignKey(
        OutSourcingAgent, on_delete=models.SET_NULL, null=True, blank=True
    )

    digital_signature = models.FileField(
        upload_to="media/Digital Signature/", null=True, blank=True
    )

    # Spouse Details
    spouse_relation = models.CharField(max_length=50, null=True, blank=True)
    spouse_name = models.CharField(max_length=50, null=True, blank=True)
    spouse_no = models.CharField(max_length=15, null=True, blank=True)
    spouse_email = models.EmailField(blank=True)
    spouse_passport = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob = models.DateField(null=True, blank=True)

    # ------------------------------ Spouse 1 -------------------------
    spouse_relation1 = models.CharField(max_length=50, null=True, blank=True)
    spouse_name1 = models.CharField(max_length=50, null=True, blank=True)
    spouse_no1 = models.CharField(max_length=15, null=True, blank=True)
    spouse_email1 = models.EmailField(blank=True)
    spouse_passport1 = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob1 = models.DateField(null=True, blank=True)
    # ------------------------------ Spouse 2 -------------------------
    spouse_relation2 = models.CharField(max_length=50, null=True, blank=True)
    spouse_name2 = models.CharField(max_length=50, null=True, blank=True)
    spouse_no2 = models.CharField(max_length=15, null=True, blank=True)
    spouse_email2 = models.EmailField(blank=True)
    spouse_passport2 = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob2 = models.DateField(null=True, blank=True)
    # ------------------------------ Spouse 3 -------------------------
    spouse_relation3 = models.CharField(max_length=50, null=True, blank=True)
    spouse_name3 = models.CharField(max_length=50, null=True, blank=True)
    spouse_no3 = models.CharField(max_length=15, null=True, blank=True)
    spouse_email3 = models.EmailField(blank=True)
    spouse_passport3 = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob3 = models.DateField(null=True, blank=True)
    # ------------------------------ Spouse 4 -------------------------
    spouse_relation4 = models.CharField(max_length=50, null=True, blank=True)
    spouse_name4 = models.CharField(max_length=50, null=True, blank=True)
    spouse_no4 = models.CharField(max_length=15, null=True, blank=True)
    spouse_email4 = models.EmailField(blank=True)
    spouse_passport4 = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob4 = models.DateField(null=True, blank=True)
    # ------------------------------ Spouse 5 -------------------------
    spouse_relation5 = models.CharField(max_length=50, null=True, blank=True)
    spouse_name5 = models.CharField(max_length=50, null=True, blank=True)
    spouse_no5 = models.CharField(max_length=15, null=True, blank=True)
    spouse_email5 = models.EmailField(blank=True)
    spouse_passport5 = models.CharField(max_length=50, null=True, blank=True)
    spouse_dob5 = models.DateField(null=True, blank=True)

    # Mailing Address
    email = models.EmailField(blank=True)
    contact = models.CharField(max_length=10)
    # country = models.CharField(max_length=100, null=True, blank=True)
    Country = CountryField()
    # Country = models.CharField(max_length=255,null=True,blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    # passport information

    passport_no = models.CharField(max_length=255)
    issue_date = models.DateField(null=True, blank=True)
    expirty_Date = models.DateField(null=True, blank=True)
    issue_country = models.CharField(max_length=255, null=True, blank=True)
    city_of_birth = models.CharField(max_length=100, null=True, blank=True)
    country_of_birth = models.CharField(max_length=244, null=True, blank=True)

    # Nationality Information
    nationality = models.CharField(max_length=100, null=True, blank=True)
    citizenship = models.CharField(max_length=100, null=True, blank=True)
    more_than_country = models.BooleanField(null=True, blank=True)
    other_country = models.BooleanField(null=True, blank=True)
    more_than_one_country = models.CharField(max_length=100, null=True, blank=True)
    studyin_in_other_country = models.CharField(max_length=100, null=True, blank=True)

    # Emergency Contact
    emergency_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_phone = models.CharField(max_length=100, null=True, blank=True)
    emergency_email = models.EmailField(blank=True)
    relation_With_applicant = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now_add=False, auto_now=True)
    registered_on = models.DateTimeField(auto_now_add=True, auto_now=False)
    case_id = models.CharField(max_length=15, unique=True, editable=False)

    archive = models.BooleanField(null=True, blank=True, default=False)

    # --------------------- Color ----------------------------

    color_code = models.CharField(
        max_length=20, choices=COLOR_CODE, blank=True, null=True
    )

    def set_spouse_name(self, spouse_names):
        self.spouse_name = json.dumps(spouse_names)

    def get_spouse_name(self):
        try:
            return json.loads(self.spouse_name) if self.spouse_name else []
        except json.JSONDecodeError:
            # Handle the error (e.g., log it) and return a default value
            return []

    def generate_case_id(self):
        # Get the current date
        current_date = datetime.date.today()

        # Get the current month abbreviation (e.g., 'SEP' for September)
        current_month_abbrev = current_date.strftime("%b").upper()

        # Get the current day as a two-digit string (e.g., '25' for the 25th day)
        current_day = current_date.strftime("%d")

        # Generate a unique serial number (e.g., '00001')
        serial_number = self.get_next_serial_number()

        # Combine all components to form the case_id
        self.case_id = f"{current_month_abbrev}{current_day}-{serial_number}"

    def get_next_serial_number(self):
        # Calculate the next serial number based on existing records
        last_enquiry = Enquiry.objects.order_by("-id").first()
        if last_enquiry and last_enquiry.case_id:
            last_serial_number = int(last_enquiry.case_id.split("-")[1])
            next_serial_number = last_serial_number + 1
        else:
            next_serial_number = 1

        # Format the serial number as a zero-padded string (e.g., '00001')
        return f"{next_serial_number:05d}"

    def generate_initials(self):
        first_initial = self.FirstName[0].upper() if self.FirstName else ""
        last_initial = self.LastName[0].upper() if self.LastName else ""
        return f"{first_initial}{last_initial}"

    class Meta:
        db_table = "Enquiry"

    def save(self, *args, **kwargs):
        if not self.enquiry_number:
            # Find the highest existing enquiry number and increment it
            highest_enquiry = Enquiry.objects.order_by("-enquiry_number").first()
            if highest_enquiry:
                last_enquiry_number = int(highest_enquiry.enquiry_number)
                self.enquiry_number = str(last_enquiry_number + 1)
            else:
                # If no existing enquiries, start with 100
                self.enquiry_number = "100"
        if not self.case_id:
            self.generate_case_id()

        super(Enquiry, self).save(*args, **kwargs)

    # def __str__(self):
    #     return str(self.id)


class Notes(models.Model):
    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.CharField(max_length=255)
    file = models.FileField(upload_to="media/Notes/", null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Notes"

    def __str__(self):
        return self.notes


class FrontWebsiteEnquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    appointment_date = models.DateTimeField(auto_created=False, null=True, blank=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="Appointment",
        null=True,
        blank=True,
    )
    country_name = models.ForeignKey(
        VisaCountry, on_delete=models.CASCADE, null=True, blank=True
    )
    category_name = models.ForeignKey(
        VisaCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    message = models.TextField(null=True, blank=True)
    image = models.FileField(
        upload_to="media/frontwebsiteenquiry/", null=True, blank=True
    )
    last_updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DocumentFiles(models.Model):
    enquiry_id = models.ForeignKey(
        Enquiry, on_delete=models.SET_NULL, null=True, blank=True
    )
    document_id = models.ForeignKey(
        Document, on_delete=models.CASCADE, null=True, blank=True
    )
    document_file = models.FileField(
        upload_to="media/Documents/", null=True, blank=True
    )
    last_updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    lastupdated_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return str(self.enquiry_id)


class Education_Summary(models.Model):
    enquiry_id = models.ForeignKey(
        Enquiry, on_delete=models.CASCADE, null=True, blank=True
    )
    country_of_education = models.CharField(max_length=100, null=True, blank=True)
    highest_level_education = models.CharField(max_length=100, null=True, blank=True)
    grading_scheme = models.CharField(max_length=100, null=True, blank=True)
    grade_avg = models.CharField(max_length=100, null=True, blank=True)
    recent_college = models.BooleanField(null=True, blank=True)
    level_education = models.CharField(max_length=100, null=True, blank=True)
    country_of_institution = models.CharField(max_length=100, null=True, blank=True)
    name_of_institution = models.CharField(max_length=100, null=True, blank=True)
    primary_language = models.CharField(max_length=100, null=True, blank=True)
    institution_from = models.DateField(null=True, blank=True)
    institution_to = models.DateField(null=True, blank=True)
    degree_Awarded = models.CharField(max_length=100, null=True, blank=True)
    degree_Awarded_On = models.CharField(max_length=100, null=True, blank=True)
    Address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    Province = models.CharField(max_length=100, null=True, blank=True)
    zipcode = models.IntegerField(null=True, blank=True)


exam_type = [
    ("PTE", "PTE"),
    ("TOEFL", "TOEFL"),
    ("IELTS", "IELTS"),
]


class TestScore(models.Model):
    enquiry_id = models.ForeignKey(
        Enquiry, on_delete=models.CASCADE, null=True, blank=True
    )
    # candidates_name = models.CharField(max_length=100)
    exam_type = models.CharField(
        max_length=100, choices=exam_type, blank=True, null=True
    )
    exam_date = models.DateField(blank=True, null=True)
    reading = models.IntegerField(blank=True)
    listening = models.IntegerField(blank=True)
    speaking = models.IntegerField(blank=True)
    writing = models.IntegerField(blank=True)
    overall_score = models.IntegerField(blank=True)


class Background_Information(models.Model):
    enquiry_id = models.ForeignKey(Enquiry, on_delete=models.CASCADE)
    background_information = models.CharField(max_length=244, blank=True, null=True)


class Work_Experience(models.Model):
    enquiry_id = models.ForeignKey(Enquiry, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=244, null=True, blank=True)
    designation = models.CharField(max_length=244, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=244, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    describe = models.TextField(null=True, blank=True)


class EnqAppointment(models.Model):
    appointment_status = [
        ("Process", "Process"),
        ("Done", "Done"),
    ]

    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=100, choices=appointment_status, default="Process"
    )
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "Enquiry Appointment"


class FAQ(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    question = models.TextField()
    answer = models.TextField(null=True, blank=True)
    last_updated_on = models.DateTimeField(auto_now_add=True)


class FollowUp(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    follow_up_status = models.CharField(
        max_length=20, choices=FOLLOWUP_STATUS_CHOICES, null=True, blank=True
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, null=True, blank=True
    )
    calendar = models.DateField(auto_created=False, null=True, blank=True)
    time = models.TimeField(auto_created=False, null=True, blank=True)
    remark = models.CharField(max_length=200, null=True, blank=True)
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now=True)


class ActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


# --------------------------- Chat Group ------------------------


class ChatGroup(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    group_member = models.ManyToManyField(CustomUser, related_name="chat_member")
    create_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_on = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.group_name


class ChatMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    message_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True
    )
    message_content = models.CharField(max_length=1000)
    filename = models.CharField(max_length=100, null=True, blank=True)
    attachment = models.FileField(
        upload_to="chat_attachments/",
        # validators=[validate_file_extension],
        null=True,
        blank=True,
    )
    msg_time = models.DateTimeField(auto_now=True)


class SuccessStory(models.Model):
    create_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    image = models.FileField(upload_to="images/general/successstories/")
    last_updated_on = models.DateTimeField(auto_now_add=True)


class News(models.Model):
    create_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    news = models.TextField()
    employee = models.BooleanField(default=False)
    agent = models.BooleanField(default=False)
    outsource_Agent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Appointment(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    start = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)


class Todo(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True
    )
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    outsourceagent = models.ForeignKey(
        OutSourcingAgent, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    is_seen = models.BooleanField(default=False)


@receiver(pre_delete, sender=Session)
def session_deleted_handler(sender, instance, **kwargs):
    user_id = instance.get_decoded().get("_auth_user_id")
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_logged_in = False
        user.save()
    except CustomUser.DoesNotExist:
        pass


@receiver(pre_delete, sender=Employee)
def delete_custom_user(sender, instance, **kwargs):
    # Disconnect the signal temporarily to avoid recursion
    pre_delete.disconnect(delete_custom_user, sender=Employee)

    # Delete the associated CustomUser before deleting the Employee
    instance.users.delete()

    # Reconnect the signal
    pre_delete.connect(delete_custom_user, sender=Employee)


@receiver(post_save, sender=CustomUser)
def create_admin_profile(sender, instance, created, **kwargs):
    # if instance.user_type==''
    if created:
        if instance.user_type == "2":
            Admin.objects.create(users=instance, contact_no="")
        elif instance.user_type == "3":  # Check if the user type is 'ManPower'
            # branch = Branch.objects.get(id=1)
            Employee.objects.create(users=instance, contact_no="", zipcode="", file="")

        elif instance.user_type == "4":  # Check if the user type is 'ManPower'
            Agent.objects.create(
                users=instance,
                contact_no="",
                zipcode="",
                activeinactive="True",
                type="",
                profile_pic="",
            )

        elif instance.user_type == "5":  # Check if the user type is 'ManPower'
            OutSourcingAgent.objects.create(
                users=instance,
                contact_no="",
                zipcode="",
                activeinactive="True",
                type="",
                profile_pic="",
            )


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == "2":
        instance.admin.save()
    if instance.user_type == "3":
        instance.employee.save()
    if instance.user_type == "4":
        instance.agent.save()
    if instance.user_type == "5":
        instance.outsourcingagent.save()
