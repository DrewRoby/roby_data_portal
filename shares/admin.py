from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Share, AccessLog

class AccessLogInline(admin.TabularInline):
    model = AccessLog
    extra = 0
    readonly_fields = ['user', 'ip_address', 'user_agent', 'accessed_at', 'password_used']
    fields = ['user', 'ip_address', 'accessed_at', 'password_used']
    max_num = 10
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'content_type_with_link', 'object_name', 'created_by', 
        'shared_with_or_public', 'permission_type', 'created_at', 
        'expires_at', 'access_count'
    ]
    list_filter = ['permission_type', 'is_public', 'created_at', 'content_type']
    search_fields = ['name', 'description', 'created_by__username', 'shared_with__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['id', 'created_at', 'access_count', 'last_accessed', 'share_url']
    fieldsets = [
        (None, {
            'fields': ['id', 'created_by', 'shared_with', 'is_public']
        }),
        ('Content', {
            'fields': ['content_type', 'object_id', 'name', 'description']
        }),
        ('Permissions', {
            'fields': ['permission_type', 'password']
        }),
        ('Expiration', {
            'fields': ['expires_at']
        }),
        ('Access Information', {
            'fields': ['access_count', 'last_accessed', 'share_url']
        }),
    ]
    inlines = [AccessLogInline]
    
    def content_type_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:contenttypes_contenttype_change', args=[obj.content_type.id]),
            obj.content_type
        )
    content_type_with_link.short_description = 'Content Type'
    
    def object_name(self, obj):
        try:
            return obj.get_object_name()
        except:
            return f"Object #{obj.object_id}"
    object_name.short_description = 'Object'
    
    def shared_with_or_public(self, obj):
        if obj.is_public:
            return format_html('<span style="color: green;">Public</span>')
        elif obj.shared_with:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=[obj.shared_with.id]),
                obj.shared_with.username
            )
        return "No one"
    shared_with_or_public.short_description = 'Shared With'
    
    def share_url(self, obj):
        url = reverse('shares:access_share', kwargs={'share_id': obj.id})
        full_url = f"{obj.id}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, full_url)
    share_url.short_description = 'Share URL'

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['share', 'user_or_anonymous', 'ip_address', 'accessed_at', 'password_used']
    list_filter = ['password_used', 'accessed_at']
    search_fields = ['share__name', 'user__username', 'ip_address']
    date_hierarchy = 'accessed_at'
    readonly_fields = ['share', 'user', 'ip_address', 'user_agent', 'accessed_at', 'password_used']
    
    def user_or_anonymous(self, obj):
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=[obj.user.id]),
                obj.user.username
            )
        return "Anonymous"
    user_or_anonymous.short_description = 'User'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False