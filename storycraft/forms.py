from django import forms
from .models import Story, Character, Setting, Plot, Scene, CharacterRelationship, Note, CharacterSceneMotivation

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Story Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Story Description', 'rows': 3}),
        }

class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ['name', 'description', 'age', 'archetype', 'attributes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Character Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Character Description', 'rows': 3}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'archetype': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Character Archetype'}),
        }
        
    # Custom field for attributes JSON
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attributes'].widget = forms.HiddenInput()
        
        # Add custom fields for common attributes
        instance = kwargs.get('instance')
        attrs = instance.attributes if instance else {}
        
        self.fields['personality'] = forms.CharField(
            required=False, 
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            initial=attrs.get('personality', '')
        )
        self.fields['appearance'] = forms.CharField(
            required=False, 
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            initial=attrs.get('appearance', '')
        )
        self.fields['goals'] = forms.CharField(
            required=False, 
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            initial=attrs.get('goals', '')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Build attributes JSON from custom fields
        attributes = {}
        for field in ['personality', 'appearance', 'goals']:
            if cleaned_data.get(field):
                attributes[field] = cleaned_data.get(field)
                
        cleaned_data['attributes'] = attributes
        return cleaned_data

class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['name', 'description', 'parent', 'attributes']
    
    def __init__(self, *args, **kwargs):
        self.story = kwargs.pop('story', None)
        super().__init__(*args, **kwargs)
        
        # Filter parent choices to settings from the same story
        if self.story:
            # Exclude the current setting from parent choices (if editing)
            if self.instance.pk:
                self.fields['parent'].queryset = Setting.objects.filter(
                    story=self.story
                ).exclude(pk=self.instance.pk)
            else:
                self.fields['parent'].queryset = Setting.objects.filter(story=self.story)
        
    # Similar custom handling for attributes as in CharacterForm
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attributes'].widget = forms.HiddenInput()
        
        instance = kwargs.get('instance')
        attrs = instance.attributes if instance else {}
        
        self.fields['geography'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=attrs.get('geography', '')
        )
        self.fields['time_period'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=attrs.get('time_period', '')
        )
        self.fields['mood'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=attrs.get('mood', '')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Build attributes JSON from custom fields
        attributes = {}
        for field in ['geography', 'time_period', 'mood']:
            if cleaned_data.get(field):
                attributes[field] = cleaned_data.get(field)
                
        cleaned_data['attributes'] = attributes
        return cleaned_data

class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ['name', 'description', 'plot_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plot Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Plot Description', 'rows': 3}),
            'plot_type': forms.Select(attrs={'class': 'form-select'}),
        }

class CharacterSceneMotivationForm(forms.ModelForm):
    """Form for character motivations within a scene."""
    class Meta:
        model = CharacterSceneMotivation
        fields = ['desire', 'obstacle', 'action']
        widgets = {
            'desire': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What does the character want?'}),
            'obstacle': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why can\'t they have it?'}),
            'action': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What do they do about it?'}),
        }

class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ['name', 'description', 'content', 'plot', 'setting', 'sequence_number', 'status', 'characters', 'metadata']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scene Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Scene Description', 'rows': 2}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Scene Content', 'rows': 10}),
            'plot': forms.Select(attrs={'class': 'form-select'}),
            'setting': forms.Select(attrs={'class': 'form-select'}),
            'sequence_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    # Custom field for characters (many-to-many)
    characters = forms.ModelMultipleChoiceField(
        queryset=Character.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        required=False,
    )
    
    # Custom field for metadata JSON
    def __init__(self, *args, **kwargs):
        story = kwargs.pop('story', None)
        super().__init__(*args, **kwargs)
        
        if story:
            # Filter related fields by story
            self.fields['plot'].queryset = Plot.objects.filter(story=story)
            self.fields['setting'].queryset = Setting.objects.filter(story=story)
            self.fields['characters'].queryset = Character.objects.filter(story=story)
        
        self.fields['metadata'].widget = forms.HiddenInput()
        
        instance = kwargs.get('instance')
        metadata = instance.metadata if instance else {}
        
        self.fields['time_of_day'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=metadata.get('time_of_day', '')
        )
        self.fields['weather'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=metadata.get('weather', '')
        )
        self.fields['mood'] = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=metadata.get('mood', '')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Build metadata JSON from custom fields
        metadata = {}
        for field in ['time_of_day', 'weather', 'mood']:
            if cleaned_data.get(field):
                metadata[field] = cleaned_data.get(field)
                
        cleaned_data['metadata'] = metadata
        return cleaned_data
        
class CharacterRelationshipForm(forms.ModelForm):
    class Meta:
        model = CharacterRelationship
        fields = ['source', 'target', 'relationship', 'description']
        widgets = {
            'source': forms.Select(attrs={'class': 'form-select'}),
            'target': forms.Select(attrs={'class': 'form-select'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship Type'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Relationship Description', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        story = kwargs.pop('story', None)
        super().__init__(*args, **kwargs)
        
        if story:
            # Filter character fields by story
            self.fields['source'].queryset = Character.objects.filter(story=story)
            self.fields['target'].queryset = Character.objects.filter(story=story)

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Add your notes here...'}),
        }