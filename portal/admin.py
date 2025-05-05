# portal/admin.py
from django.contrib import admin
from .models import UserProfile, EmailVerificationToken, App, UserAppAccess, ActivityLog

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'job_title', 'is_email_verified')
    search_fields = ('user__username', 'user__email', 'company')
    list_filter = ('is_email_verified',)

class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_expired')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'expires_at')

class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'app_id', 'is_default', 'order')
    search_fields = ('name', 'app_id', 'description')
    list_filter = ('is_default',)
    list_editable = ('order',)

class UserAppAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'app', 'granted_date')
    list_filter = ('app', 'granted_date')
    search_fields = ('user__username', 'user__email', 'app__name')
    date_hierarchy = 'granted_date'

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_name', 'activity_type', 'timestamp')
    list_filter = ('app_name', 'activity_type', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'app_name', 'activity_type', 'description', 'timestamp')
    date_hierarchy = 'timestamp'

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
admin.site.register(App, AppAdmin)
admin.site.register(UserAppAccess, UserAppAccessAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)