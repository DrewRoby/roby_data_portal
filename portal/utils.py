from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
from django.utils import timezone

def send_templated_email(template_name, context, subject, recipient_list, from_email=None):
    """
    Send an email using HTML template with a plain text fallback.
    
    Args:
        template_name (str): Path to the email template
        context (dict): Context data for the template
        subject (str): Email subject
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): Sender email address. Defaults to settings.DEFAULT_FROM_EMAIL.
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list
    )
    
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        # Log the error
        print(f"Error sending email: {e}")
        return False

def generate_unique_token():
    """Generate a unique UUID token."""
    return uuid.uuid4()

def is_token_expired(timestamp, hours=48):
    """
    Check if a timestamp is older than a specified number of hours.
    
    Args:
        timestamp (datetime): Timestamp to check
        hours (int, optional): Number of hours. Defaults to 48.
    
    Returns:
        bool: True if expired, False otherwise
    """
    expiration_time = timestamp + timezone.timedelta(hours=hours)
    return timezone.now() > expiration_time