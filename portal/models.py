from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    """Extended user profile information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class EmailVerificationToken(models.Model):
    """Stores tokens for email verification."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Verification token for {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set expiration date to 48 hours from creation
        if not self.expires_at:
            self.expires_at = self.created_at + timezone.timedelta(hours=48)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

class App(models.Model):
    """Stores information about available applications in the portal."""
    app_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Icon class or name")
    background_color = models.CharField(max_length=20, default="#ffffff")
    link = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    # app_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_ownership')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order', 'name']

class UserAppAccess(models.Model):
    """Tracks which applications a user has access to."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_access_new')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    granted_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'app')
        verbose_name_plural = "User App Access"
    
    def __str__(self):
        return f"{self.user.username} - {self.app.name}"

class ActivityLog(models.Model):
    """Logs user activity across applications."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    app_name = models.CharField(max_length=20, choices=[])  # We'll update this to use App choices
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def save(self, *args, **kwargs):
        # Update app_name choices to use App model if it exists
        if not ActivityLog._meta.get_field('app_name').choices:
            try:
                # Attempt to update choices dynamically
                apps = App.objects.all()
                if apps.exists():
                    ActivityLog._meta.get_field('app_name').choices = [
                        (app.app_id, app.name) for app in apps
                    ]
            except:
                # If App model doesn't exist yet, use empty choices
                pass
        super().save(*args, **kwargs)