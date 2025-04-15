from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Story(models.Model):
    """Main container for a story project."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Stories"


class Character(models.Model):
    """A character in a story."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='characters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Character attributes
    age = models.IntegerField(blank=True, null=True)
    archetype = models.CharField(max_length=100, blank=True, null=True)
    
    # Character metadata as JSON
    attributes = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.story.title})"

    def get_all_relationships(self):
	    """Get all relationships this character is involved in."""
	    outgoing = self.outgoing_relationships.all()
	    incoming = self.incoming_relationships.all()
	    return list(outgoing) + list(incoming)


class CharacterRelationship(models.Model):
	"""Relationship between two characters."""
	source = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='outgoing_relationships')
	target = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='incoming_relationships')
	relationship = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)

	def __str__(self):
	    return f"{self.source.name} -> {self.relationship} -> {self.target.name}"


class Setting(models.Model):
	"""A location where scenes take place."""
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)
	story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='settings')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Setting metadata as JSON
	attributes = models.JSONField(default=dict, blank=True)

	def __str__(self):
	    return f"{self.name} ({self.story.title})"


class Plot(models.Model):
	"""A narrative arc within a story."""
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)
	story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='plots')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Plot type and status
	PLOT_TYPES = (
	    ('main', 'Main Plot'),
	    ('subplot', 'Subplot'),
	    ('character_arc', 'Character Arc'),
	)
	plot_type = models.CharField(max_length=20, choices=PLOT_TYPES, default='subplot')

	def __str__(self):
	    return f"{self.name} ({self.story.title})"

	def get_related_characters(self):
	    """Get all characters involved in scenes connected to this plot."""
	    character_ids = self.scenes.values_list('characters', flat=True).distinct()
	    return Character.objects.filter(id__in=character_ids).distinct()

class Scene(models.Model):
	"""An individual segment of a story."""
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)
	content = models.TextField(blank=True, null=True)  # The actual scene text
	story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='scenes')
	plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name='scenes')
	setting = models.ForeignKey(Setting, on_delete=models.CASCADE, related_name='scenes')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Scene position in the story
	sequence_number = models.IntegerField(default=0)  # For ordering scenes

	# Scene metadata
	STATUS_CHOICES = (
	    ('draft', 'Draft'),
	    ('revised', 'Revised'),
	    ('final', 'Final'),
	)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

	# Many-to-many relationship with characters
	characters = models.ManyToManyField(Character, related_name='scenes')

	# Additional scene metadata
	metadata = models.JSONField(default=dict, blank=True)  # For things like mood, time of day, etc.

	class Meta:
	    ordering = ['sequence_number']

	def __str__(self):
	    return f"{self.name} ({self.story.title})"