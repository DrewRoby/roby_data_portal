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

class AppAccess(models.Model):
    """Tracks which applications a user has access to."""
    APP_CHOICES = (
        ('analytics', 'Data Analytics'),
        ('visualization', 'Data Visualization'),
        ('etl', 'ETL Manager'),
        ('warehouse', 'Data Warehouse'),
        ('ml', 'ML Workbench'),
        ('governance', 'Data Governance'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_access')
    app_name = models.CharField(max_length=20, choices=APP_CHOICES)
    granted_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'app_name')
        verbose_name_plural = "App Access"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_app_name_display()}"

class ActivityLog(models.Model):
    """Logs user activity across applications."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    app_name = models.CharField(max_length=20, choices=AppAccess.APP_CHOICES)
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"