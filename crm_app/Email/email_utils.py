from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import subprocess
from django.core.mail import EmailMultiAlternatives
from email.mime.base import MIMEBase
from email import encoders


# def generate_pdf(html_content):
#     # Use wkhtmltopdf to generate a PDF from HTML content
#     command = ["wkhtmltopdf", "-", "-"]
#     process = subprocess.Popen(
#         command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
#     )
#     pdf_content, errors = process.communicate(input=html_content.encode("utf-8"))
#     process.wait()

#     if errors:
#         # Handle any errors (e.g., print them for debugging)
#         print(errors.decode("utf-8"))

#     return pdf_content


def send_congratulatory_email(firstname, lastname, email, password, user_type):
    subject = "Congratulations! Your Account is Created"

    # Render the HTML template with dynamic content
    html_message = render_to_string(
        "email_template.html",
        {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "password": password,
            "user_type": user_type,
        },
    )

    # Create a plain text version of the HTML content (for clients that don't support HTML)
    plain_message = strip_tags(html_message)

    # Change this to your email
    recipient_list = [email]  # List of recipient email addresses

    send_mail(
        subject,
        plain_message,
        from_email=None,
        recipient_list=recipient_list,
        html_message=html_message,
    )


from crm_app.models import CustomUser

# ------------------------------- Package email ----------------------------
users = CustomUser.objects.all()
email_list = []

# Iterate through each user and append their email to the list
for user in users:
    email_list.append(user.email)


def send_package_email(title, country):
    subject = "Greetings! New Product Added ."

    # Render the HTML template with dynamic content
    html_message = render_to_string(
        "packagemail.html",
        {
            "title": title,
            "country": country,
        },
    )

    # Create a plain text version of the HTML content (for clients that don't support HTML)
    plain_message = strip_tags(html_message)

    # Change this to your email
    recipient_list = email_list

    send_mail(
        subject,
        plain_message,
        from_email=None,
        recipient_list=recipient_list,
        html_message=html_message,
    )
