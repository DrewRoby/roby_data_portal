from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Share, ShareEmailNotification
import logging

logger = logging.getLogger(__name__)

class ShareEmailService:
    """Service class for handling share email notifications."""
    
    @staticmethod
    def get_email_template_name(shared_object):
        """
        Determine the email template based on the shared object's app.
        Returns the template name to use for the email.
        """
        app_name = shared_object._meta.app_label
        template_name = f'shares/email/{app_name}_share.html'
        
        # Template mapping for known apps
        template_map = {
            'events': 'shares/email/events_share.html',
            'storycraft': 'shares/email/storycraft_share.html',
        }
        
        return template_map.get(app_name, 'shares/email/generic_share.html')
    
    @staticmethod
    def send_share_notification(share, email_address, sent_by, request=None):
        """
        Send a single email notification for a share.
        
        Args:
            share: Share instance
            email_address: Recipient email address
            sent_by: User who is sending the notification
            request: HttpRequest instance for building absolute URLs
        
        Returns:
            tuple: (success: bool, notification: ShareEmailNotification or None)
        """
        try:
            # Check if notification already exists (prevent duplicates)
            existing_notification = ShareEmailNotification.objects.filter(
                share=share,
                email_address=email_address
            ).first()
            
            if existing_notification:
                logger.info(f"Notification already exists for {email_address} and share {share.id}")
                return False, existing_notification
            
            # Build the share URL
            if request:
                share_url = request.build_absolute_uri(share.get_absolute_url())
            else:
                # Fallback if no request available
                share_url = f"https://dev.robydata.com{share.get_absolute_url()}"
            
            # Get the appropriate email template
            template_name = ShareEmailService.get_email_template_name(share.shared_object)
            
            # Prepare email context
            context = {
                'share': share,
                'object': share.shared_object,
                'share_url': share_url,
                'sent_by': sent_by,
            }
            
            # Render email content
            html_message = render_to_string(template_name, context)
            
            # Create plain text version (simplified)
            plain_message = f"""
Hello!

{sent_by.get_full_name() or sent_by.username} has shared something with you: {share.shared_object.get_share_title()}

{share.description if share.description else ''}

View the shared content here: {share_url}

This email was sent from Roby Data Services.
            """.strip()
            
            # Determine subject based on object type
            subject = ShareEmailService.get_email_subject(share)
            
            # Send the email
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                html_message=html_message,
                fail_silently=False
            )
            
            if success:
                # Create notification record
                notification = ShareEmailNotification.objects.create(
                    share=share,
                    email_address=email_address,
                    sent_by=sent_by,
                    email_subject=subject
                )
                logger.info(f"Email sent successfully to {email_address} for share {share.id}")
                return True, notification
            else:
                logger.error(f"Failed to send email to {email_address} for share {share.id}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error sending email to {email_address} for share {share.id}: {str(e)}")
            return False, None
    
    @staticmethod
    def get_email_subject(share):
        """Generate email subject based on the shared object type."""
        app_name = share.shared_object._meta.app_label
        object_title = share.shared_object.get_share_title()
        
        subject_map = {
            'events': f'Event Invitation: {object_title}',
            'storycraft': f'Story Shared: {object_title}',
        }
        
        return subject_map.get(app_name, f'Shared Content: {object_title}')
    
    @staticmethod
    def send_multiple_notifications(share, email_addresses, sent_by, request=None):
        """
        Send notifications to multiple email addresses.
        
        Args:
            share: Share instance
            email_addresses: List of email addresses
            sent_by: User sending the notifications
            request: HttpRequest instance
            
        Returns:
            dict: Results with success/failure counts and details
        """
        results = {
            'success_count': 0,
            'failure_count': 0,
            'duplicate_count': 0,
            'notifications': [],
            'errors': []
        }
        
        for email in email_addresses:
            success, notification = ShareEmailService.send_share_notification(
                share, email, sent_by, request
            )
            
            if success:
                results['success_count'] += 1
                results['notifications'].append(notification)
            elif notification:  # Existing notification (duplicate)
                results['duplicate_count'] += 1
            else:  # Failed to send
                results['failure_count'] += 1
                results['errors'].append(f"Failed to send to {email}")
        
        return results
    
    @staticmethod
    def resend_notification(share, email_address, sent_by, request=None):
        """
        Resend a notification by deleting the existing record and sending a new one.
        
        Args:
            share: Share instance
            email_address: Email address to resend to
            sent_by: User sending the notification
            request: HttpRequest instance
            
        Returns:
            tuple: (success: bool, notification: ShareEmailNotification or None)
        """
        # Delete existing notification if it exists
        ShareEmailNotification.objects.filter(
            share=share,
            email_address=email_address
        ).delete()
        
        # Send new notification
        return ShareEmailService.send_share_notification(
            share, email_address, sent_by, request
        )