from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone
import uuid

class ShareableInterface(models.Model):
    """
    Abstract model that provides an interface for shareable objects.
    Any model that needs to be shareable should inherit from this.
    """
    class Meta:
        abstract = True
    
    def get_share_url(self):
        """
        Returns the URL for viewing this object when shared.
        Must be implemented by all shareable models.
        """
        raise NotImplementedError("Subclasses must implement get_share_url()")
    
    def get_absolute_url(self):
        """
        Returns the canonical URL for viewing this object.
        Must be implemented by all shareable models.
        """
        raise NotImplementedError("Subclasses must implement get_absolute_url()")
    
    def get_share_title(self):
        """
        Returns a human-readable title for the shared object.
        Must be implemented by all shareable models.
        """
        raise NotImplementedError("Subclasses must implement get_share_title()")
    
    def get_share_description(self):
        """
        Returns a description for the shared object.
        Can be overridden for custom descriptions.
        """
        return f"Shared {self._meta.verbose_name}"
    
    def get_content_type(self):
        """
        Returns the ContentType for this model.
        """
        return ContentType.objects.get_for_model(self)
    
    def get_share_permissions(self, user=None):
        """
        Returns the permissions a specific user has for this object.
        """
        # Check if there's a share for this object
        content_type = self.get_content_type()
        object_id = self.pk
        
        # First, check public shares
        try:
            public_share = Share.objects.get(
                content_type=content_type,
                object_id=object_id,
                is_public=True,
                expires_at__gt=timezone.now()
            )
            return public_share.permission_type
        except Share.DoesNotExist:
            pass
        
        # If no public share and no user, return None
        if not user or user.is_anonymous:
            return None
            
        # If user is the owner, return 'ADMIN'
        if hasattr(self, 'user') and self.user == user:
            return 'ADMIN'
        
        # Check for user-specific shares
        try:
            share = Share.objects.get(
                content_type=content_type,
                object_id=object_id,
                shared_with=user,
                is_public=False,
                expires_at__gt=timezone.now()
            )
            return share.permission_type
        except Share.DoesNotExist:
            return None


class Share(models.Model):
    """
    Represents a shared resource with specific permissions.
    """
    PERMISSION_CHOICES = [
        ('VIEW', 'View Only'),
        ('COMMENT', 'Comment'),
        ('EDIT', 'Edit'),
        ('ADMIN', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For targeting any shareable model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    shared_object = GenericForeignKey('content_type', 'object_id')
    
    # Share settings
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_received', null=True, blank=True)
    permission_type = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='VIEW')
    is_public = models.BooleanField(default=False)
    password = models.CharField(max_length=255, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Optional metadata
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Share"
        verbose_name_plural = "Shares"
        unique_together = [['content_type', 'object_id', 'shared_with']]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        if self.is_public:
            return f"Public share: {self.get_object_name()} ({self.permission_type})"
        return f"Share with {self.shared_with}: {self.get_object_name()} ({self.permission_type})"
    
    def get_object_name(self):
        """Returns a human-readable name for the shared object."""
        if self.shared_object and hasattr(self.shared_object, 'get_share_title'):
            return self.shared_object.get_share_title()
        return f"{self.content_type.model} #{self.object_id}"
    
    def get_absolute_url(self):
        """Returns the URL for accessing this share."""
        return reverse('shares:access_share', kwargs={'share_id': self.id})
    
    def increment_access_count(self):
        """Increments the access count and updates the last accessed timestamp."""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])
    
    def is_expired(self):
        """Checks if the share has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_accessible_by(self, user):
        """
        Checks if a user can access this share.
        Public shares are accessible by anyone.
        """
        if self.is_expired():
            return False
            
        if self.is_public:
            return True
            
        if not user or user.is_anonymous:
            return False
            
        if user == self.created_by:
            return True
            
        return user == self.shared_with
    
    def save(self, *args, **kwargs):
        # Set default expiration if not provided
        if not self.expires_at:
            # Default to 30 days from now
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)


class AccessLog(models.Model):
    """
    Logs each access to a shared object.
    """
    share = models.ForeignKey(Share, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    password_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-accessed_at']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"Access by {user_str} at {self.accessed_at}"