from django import forms
from django.contrib.auth.models import User
from .models import Event, EventInvitation, AgendaItem, AgendaComment, Space


class EventForm(forms.ModelForm):
    """Form for creating and editing events."""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'date', 'start_time', 
            'end_time', 'location', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['end_time'].required = False
        self.fields['location'].required = False
        self.fields['description'].required = False


class RSVPForm(forms.ModelForm):
    """Form for updating RSVP status."""
    
    class Meta:
        model = EventInvitation
        fields = ['rsvp_status']
        widgets = {
            'rsvp_status': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the choices to be more user-friendly
        self.fields['rsvp_status'].choices = [
            ('yes', 'Yes, I\'ll attend'),
            ('tentative', 'Maybe'),
            ('no', 'Can\'t make it'),
        ]


class AgendaItemForm(forms.ModelForm):
    """Form for creating agenda items (suggestions or direct additions)."""
    
    duration_hours = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'})
    )
    duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'})
    )
    
    class Meta:
        model = AgendaItem
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        
        # If editing existing item, populate duration fields
        if self.instance and self.instance.pk:
            total_minutes = self.instance.duration_minutes
            self.fields['duration_hours'].initial = total_minutes // 60
            self.fields['duration_minutes'].initial = total_minutes % 60
    
    def clean(self):
        cleaned_data = super().clean()
        hours = cleaned_data.get('duration_hours', 0)
        minutes = cleaned_data.get('duration_minutes', 0)
        
        # Convert to total minutes
        total_minutes = (hours * 60) + minutes
        
        if total_minutes <= 0:
            raise forms.ValidationError("Duration must be greater than 0 minutes.")
        
        # Store total minutes in the field that will be saved
        cleaned_data['duration_minutes'] = total_minutes
        
        return cleaned_data


class AgendaCommentForm(forms.ModelForm):
    """Form for adding comments to agenda items."""
    
    class Meta:
        model = AgendaComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...'
            })
        }


class SpaceForm(forms.ModelForm):
    """Form for creating and editing spaces."""
    
    class Meta:
        model = Space
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class MoveAgendaItemForm(forms.Form):
    """Form for moving agenda items between spaces."""
    
    target_space = forms.ModelChoiceField(
        queryset=Space.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select target space..."
    )
    
    def __init__(self, event, exclude_space=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show normal spaces (not suggestion boxes) as targets
        queryset = event.spaces.filter(space_type='normal')
        
        # Exclude current space if specified
        if exclude_space:
            queryset = queryset.exclude(pk=exclude_space.pk)
        
        self.fields['target_space'].queryset = queryset


class BulkRSVPForm(forms.Form):
    """Form for event creators to see all RSVPs at once."""
    
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add a field for each invitation
        for invitation in event.invitations.all():
            field_name = f"rsvp_{invitation.id}"
            self.fields[field_name] = forms.ChoiceField(
                choices=EventInvitation.RSVP_CHOICES,
                initial=invitation.rsvp_status,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
                label=invitation.invitee.get_full_name() or invitation.invitee.username
            )
    
    def save(self, event):
        """Update all RSVP statuses based on form data."""
        updated_count = 0
        
        for invitation in event.invitations.all():
            field_name = f"rsvp_{invitation.id}"
            new_status = self.cleaned_data.get(field_name)
            
            if new_status and new_status != invitation.rsvp_status:
                invitation.rsvp_status = new_status
                invitation.save()
                updated_count += 1
        
        return updated_count