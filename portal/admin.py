from django.contrib import admin
from .models import UserProfile, EmailVerificationToken, AppAccess, ActivityLog

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'job_title', 'is_email_verified')
    search_fields = ('user__username', 'user__email', 'company')
    list_filter = ('is_email_verified',)

class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_expired')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'expires_at')

class AppAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_name', 'granted_date')
    list_filter = ('app_name', 'granted_date')
    search_fields = ('user__username', 'user__email')

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_name', 'activity_type', 'timestamp')
    list_filter = ('app_name', 'activity_type', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'app_name', 'activity_type', 'description', 'timestamp')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
admin.site.register(AppAccess, AppAccessAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)