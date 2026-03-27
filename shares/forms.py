# shares/forms.py - Updated ShareForm

from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
from .models import Share, ShareEmailNotification

class ShareForm(forms.ModelForm):
    """
    Form for creating and editing shares with email notification support.
    """
    DURATION_CHOICES = [
        ('1', '1 Day'),
        ('7', '7 Days'),
        ('30', '30 Days'),
        ('90', '90 Days'),
        ('365', '1 Year'),
        ('custom', 'Custom Date'),
    ]
    
    shared_with_username = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username to share with'})
    )
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    custom_expiry = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    # New field for email recipients
    email_recipients = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter email addresses separated by commas (e.g., user1@example.com, user2@example.com)'
        }),
        help_text='Email addresses to notify about this public share. Separate multiple emails with commas.',
        label='Email Recipients'
    )
    
    class Meta:
        model = Share
        fields = ['name', 'description', 'permission_type', 'is_public', 'password', 'email_recipients']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permission_type': forms.Select(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.share_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        # If editing an existing share, populate the username field
        if self.instance and self.instance.pk and self.instance.shared_with:
            self.fields['shared_with_username'].initial = self.instance.shared_with.username
    
    def clean_email_recipients(self):
        """Validate and clean email recipients."""
        email_recipients = self.cleaned_data.get('email_recipients', '').strip()
        
        if not email_recipients:
            return email_recipients
        
        # Split by comma and clean up
        emails = [email.strip() for email in email_recipients.split(',') if email.strip()]
        
        # Validate each email
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        invalid_emails = []
        valid_emails = []
        
        for email in emails:
            if email_regex.match(email):
                if email not in valid_emails:  # Remove duplicates
                    valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise ValidationError(
                f"Invalid email addresses: {', '.join(invalid_emails)}"
            )
        
        return ', '.join(valid_emails)
    
    def clean(self):
        cleaned_data = super().clean()
        is_public = cleaned_data.get('is_public')
        shared_with_username = cleaned_data.get('shared_with_username')
        email_recipients = cleaned_data.get('email_recipients')
        
        # Validate that either is_public is True or shared_with is provided
        if not is_public and not shared_with_username:
            self.add_error(
                'shared_with_username', 
                'You must either make the share public or specify a user to share with.'
            )
        
        # Email recipients are only valid for public shares
        if email_recipients and not is_public:
            self.add_error(
                'email_recipients',
                'Email notifications are only available for public shares.'
            )
        
        # Handle expiration date
        duration = cleaned_data.get('duration')
        custom_expiry = cleaned_data.get('custom_expiry')
        
        if duration == 'custom' and not custom_expiry:
            self.add_error('custom_expiry', 'Custom expiration date is required.')
        elif custom_expiry and custom_expiry < timezone.now():
            self.add_error('custom_expiry', 'Expiration date cannot be in the past.')
        
        return cleaned_data
    
    def get_email_list(self):
        """Return a list of email addresses from the cleaned email_recipients field."""
        email_recipients = self.cleaned_data.get('email_recipients', '')
        if not email_recipients:
            return []
        return [email.strip() for email in email_recipients.split(',') if email.strip()]


class ResendEmailForm(forms.Form):
    """
    Simple form for resending email to a specific address.
    """
    email_address = forms.EmailField(
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.share = kwargs.pop('share', None)
        self.email_address = kwargs.pop('email_address', None)
        super().__init__(*args, **kwargs)
        
        if self.email_address:
            self.fields['email_address'].initial = self.email_address