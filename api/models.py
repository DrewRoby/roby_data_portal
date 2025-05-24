from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class APIUsageLog(models.Model):
    """Track API usage for billing and monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    request_data = models.JSONField(blank=True, null=True)  # Store request params for debugging
    response_count = models.IntegerField(default=0)  # Number of results returned
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
