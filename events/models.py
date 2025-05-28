# events/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from shares.models import ShareableInterface, Share



class Event(models.Model, ShareableInterface):
    """Main event model that can be shared via the shares system."""
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=300, blank=True)
    
    # Public access
    is_public = models.BooleanField(
        default=False, 
        help_text="Allow anyone to view this event (login required for RSVP/comments)"
    )
    
    # Event management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.date}"
    
    @property
    def is_past(self):
        """Check if the event is in the past."""
        event_datetime = timezone.datetime.combine(self.date, self.start_time)
        if timezone.is_naive(event_datetime):
            event_datetime = timezone.make_aware(event_datetime)
        return event_datetime < timezone.now()
    
    def get_absolute_url(self):
        """Required by ShareableInterface."""
        return reverse('events:event_detail', kwargs={'pk': self.pk})
    
    def get_share_url(self):
        """Required by ShareableInterface - same as absolute URL for events."""
        return self.get_absolute_url()
    
    def get_share_title(self):
        """Required by ShareableInterface."""
        return self.title
    
    def get_share_description(self):
        """Required by ShareableInterface."""
        return f"Event on {self.date} at {self.location}" if self.location else f"Event on {self.date}"
    
    @property
    def user(self):
        """Required for owner checking in shares system."""
        return self.created_by

    def get_verbose_name(self):
        """Get the verbose name for templates (since _meta is not accessible)."""
        return self._meta.verbose_name
    
    def get_user_permission(self, user):
        """
        Get the effective permission level a user has for this event.
        Combines public access, ownership, and share permissions.
        """
        if not user or user.is_anonymous:
            return 'VIEW' if self.is_public else None
            
        # Owner has admin rights
        if self.created_by == user:
            return 'ADMIN'
            
        # Check share permissions
        share_permission = self.get_share_permissions(user)
        if share_permission:
            return share_permission
            
        # Public events allow viewing for authenticated users
        if self.is_public:
            return 'VIEW'
            
        return None
    
    def can_user_suggest_agenda_items(self, user):
        """
        Check if user can suggest agenda items.
        Requires: RSVP'd + EDIT permission or higher
        """
        if not user or user.is_anonymous:
            return False
            
        # Check permission level
        permission = self.get_user_permission(user)
        if permission not in ['EDIT', 'ADMIN']:
            return False
            
        # Check RSVP status
        try:
            invitation = EventInvitation.objects.get(event=self, invitee=user)
            return invitation.rsvp_status == 'yes'
        except EventInvitation.DoesNotExist:
            return False
    
    def can_user_move_suggestions(self, user):
        """
        Check if user can move items from suggestion box to agenda.
        Requires: ADMIN permission
        """
        permission = self.get_user_permission(user)
        return permission == 'ADMIN'

class EventInvitation(models.Model):
    """
    Tracks RSVP status for event invitations.
    References the shares system for permission management.
    """
    
    RSVP_CHOICES = [
        ('pending', 'Pending'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ('tentative', 'Tentative'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_invitations')
    share = models.OneToOneField(
        Share, 
        on_delete=models.CASCADE, 
        related_name='event_invitation',
        help_text="References the share that created this invitation"
    )
    
    rsvp_status = models.CharField(max_length=10, choices=RSVP_CHOICES, default='pending')
    rsvp_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'invitee']
    
    def __str__(self):
        return f"{self.invitee.username} - {self.event.title} ({self.rsvp_status})"
    
    def save(self, *args, **kwargs):
        if self.rsvp_status != 'pending' and not self.rsvp_date:
            self.rsvp_date = timezone.now()
        super().save(*args, **kwargs)


class Space(models.Model):
    """
    Represents a space/room/stage within an event.
    Each space has its own agenda.
    """
    
    SPACE_TYPES = [
        ('normal', 'Normal Space'),
        ('suggestion_box', 'Suggestion Box'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='spaces')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    space_type = models.CharField(max_length=20, choices=SPACE_TYPES, default='normal')
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['event', 'name']
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"
    
    @property
    def total_duration_minutes(self):
        """Calculate total duration of all agenda items in this space."""
        return self.agenda_items.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
    
    @property
    def total_duration_display(self):
        """Return duration in HH:MM format."""
        total_minutes = self.total_duration_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"


class AgendaItem(models.Model):
    """
    Individual agenda items within a space.
    Can be suggested items (in suggestion box) or confirmed agenda items.
    """
    
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='agenda_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Duration in minutes"
    )
    
    # Ordering and metadata
    order = models.PositiveIntegerField(default=0)
    suggested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        help_text="User who suggested this item (if applicable)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.space.name}: {self.title}"
    
    @property
    def duration_display(self):
        """Return duration in HH:MM format."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def can_user_comment(self, user, event):
        """
        Check if user can comment on this agenda item.
        Any invitee can comment, regardless of RSVP status.
        """
        if not user or user.is_anonymous:
            return False
            
        # Event owner can always comment
        if event.created_by == user:
            return True
            
        # Anyone with any permission level can comment
        permission = event.get_user_permission(user)
        return permission is not None


class AgendaComment(models.Model):
    """
    Comments on agenda items.
    Any invitee can comment regardless of RSVP status.
    """
    
    agenda_item = models.ForeignKey(AgendaItem, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.agenda_item.title}"