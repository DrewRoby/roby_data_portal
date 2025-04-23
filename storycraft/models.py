from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType





class Story(models.Model):
    """Main container for a story project."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = GenericRelation('Note')
    
    def __str__(self):
        return self.title
    
    def create_default_plot(self):
        """Create a default main plot for this story."""
        return Plot.objects.create(
            name="Main Plot",
            description="The primary storyline.",
            story=self,
            plot_type='main'
        )

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

    # Notes
    notes = GenericRelation('Note')

    
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
    notes = GenericRelation('Note')

    def __str__(self):
        return f"{self.source.name} -> {self.relationship} -> {self.target.name}"


class Setting(models.Model):
    """A location where scenes take place."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='settings')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', 
                               null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Setting metadata as JSON
    attributes = models.JSONField(default=dict, blank=True)
    notes = GenericRelation('Note')

    def __str__(self):
        return f"{self.name} ({self.story.title})"
    
    def get_all_children(self):
        """Get all subsettings of this setting."""
        return self.children.all()


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
    notes = GenericRelation('Note')

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
    notes = GenericRelation('Note')

    class Meta:
        ordering = ['sequence_number']

    def __str__(self):
        return f"{self.name} ({self.story.title})"


class Note(models.Model):
    """Notes that can be attached to any entity in the system."""
    # Content of the note
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Generic foreign key to allow attaching to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # The user who created the note
    user = models.ForeignKey(User, on_delete=models.CASCADE)
  
    def __str__(self):
        return f"Note on {self.content_type.model}: {self.content_object}"


class CharacterSceneMotivation(models.Model):
    """Tracks character motivations, obstacles, and actions within a scene."""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='scene_motivations')
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='character_motivations')
    desire = models.TextField(blank=True, null=True, help_text="What does the character want in this scene?")
    obstacle = models.TextField(blank=True, null=True, help_text="What prevents the character from getting what they want?")
    action = models.TextField(blank=True, null=True, help_text="What does the character do about their obstacle?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['character', 'scene']
        verbose_name = "Character Motivation"
        verbose_name_plural = "Character Motivations"
    
    def __str__(self):
        return f"{self.character.name}'s motivation in {self.scene.name}"