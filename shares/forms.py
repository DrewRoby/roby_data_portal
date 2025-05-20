from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Share

class ShareForm(forms.ModelForm):
    """
    Form for creating and editing shares.
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
    
    class Meta:
        model = Share
        fields = ['name', 'description', 'permission_type', 'is_public', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permission_type': forms.Select(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an existing share, populate the username field
        if self.instance and self.instance.pk and self.instance.shared_with:
            self.fields['shared_with_username'].initial = self.instance.shared_with.username
    
    def clean(self):
        cleaned_data = super().clean()
        is_public = cleaned_data.get('is_public')
        shared_with_username = cleaned_data.get('shared_with_username')
        
        # Validate that either is_public is True or shared_with is provided
        if not is_public and not shared_with_username:
            self.add_error(
                'shared_with_username', 
                'You must either make the share public or specify a user to share with.'
            )
        
        # Handle expiration date
        duration = cleaned_data.get('duration')
        custom_expiry = cleaned_data.get('custom_expiry')
        
        if duration == 'custom' and not custom_expiry:
            self.add_error('custom_expiry', 'Custom expiration date is required.')
        elif custom_expiry and custom_expiry < timezone.now():
            self.add_error('custom_expiry', 'Expiration date cannot be in the past.')
        
        return cleaned_data
    
    def save(self, commit=True):
        share = super().save(commit=False)
        
        # Process shared_with field
        shared_with_username = self.cleaned_data.get('shared_with_username')
        
        # Clear shared_with if it's a public share
        if self.cleaned_data.get('is_public'):
            share.shared_with = None
        # Otherwise, try to find the user by username
        elif shared_with_username:
            try:
                user = User.objects.get(username=shared_with_username)
                share.shared_with = user
            except User.DoesNotExist:
                if commit:
                    self.add_error('shared_with_username', f'User "{shared_with_username}" does not exist.')
                return share
        
        if commit:
            share.save()
        return share

class SharePasswordForm(forms.Form):
    """
    Form for entering a password to access a protected share.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the password to access this shared content'
        }),
        required=True
    )