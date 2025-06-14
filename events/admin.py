from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Event, EventInvitation, Space, AgendaItem, AgendaComment


class SpaceInline(admin.TabularInline):
    model = Space
    extra = 0
    fields = ['name', 'space_type', 'order']
    readonly_fields = []


class EventInvitationInline(admin.TabularInline):
    model = EventInvitation
    extra = 0
    fields = ['invitee', 'rsvp_status', 'rsvp_date']
    readonly_fields = ['rsvp_date']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'date', 'start_time', 'location', 'created_by', 
        'is_public', 'invitation_count', 'rsvp_summary'
    ]
    list_filter = ['is_public', 'date', 'created_by']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'date'
    
    fieldsets = [
        (None, {
            'fields': ['title', 'description']
        }),
        ('Schedule', {
            'fields': ['date', 'start_time', 'end_time', 'location']
        }),
        ('Access & Permissions', {
            'fields': ['is_public', 'created_by']
        }),
    ]
    
    inlines = [SpaceInline, EventInvitationInline]
    
    def invitation_count(self, obj):
        return obj.invitations.count()
    invitation_count.short_description = 'Invitations'
    
    def rsvp_summary(self, obj):
        counts = obj.invitations.values('rsvp_status').annotate(
            count=admin.models.Count('rsvp_status')
        )
        summary = {item['rsvp_status']: item['count'] for item in counts}
        
        parts = []
        if summary.get('yes', 0):
            parts.append(f"✓ {summary['yes']}")
        if summary.get('tentative', 0):
            parts.append(f"? {summary['tentative']}")
        if summary.get('no', 0):
            parts.append(f"✗ {summary['no']}")
        if summary.get('pending', 0):
            parts.append(f"⏳ {summary['pending']}")
            
        return " | ".join(parts) if parts else "No RSVPs"
    rsvp_summary.short_description = 'RSVP Status'


class AgendaItemInline(admin.TabularInline):
    model = AgendaItem
    extra = 0
    fields = ['title', 'duration_minutes', 'order', 'suggested_by']
    readonly_fields = ['suggested_by']


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'space_type', 'order', 'item_count', 'total_duration_display']
    list_filter = ['space_type', 'event__date']
    search_fields = ['name', 'event__title']
    
    inlines = [AgendaItemInline]
    
    def item_count(self, obj):
        return obj.agenda_items.count()
    item_count.short_description = 'Items'


class AgendaCommentInline(admin.TabularInline):
    model = AgendaComment
    extra = 0
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']


@admin.register(AgendaItem)
class AgendaItemAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'space', 'duration_display', 'order', 
        'suggested_by', 'comment_count'
    ]
    list_filter = ['space__space_type', 'space__event__date', 'suggested_by']
    search_fields = ['title', 'description', 'space__name', 'space__event__title']
    
    fieldsets = [
        (None, {
            'fields': ['space', 'title', 'description']
        }),
        ('Scheduling', {
            'fields': ['duration_minutes', 'order']
        }),
        ('Metadata', {
            'fields': ['suggested_by'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [AgendaCommentInline]
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'


@admin.register(EventInvitation)
class EventInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'invitee', 'rsvp_status', 'permission_level', 
        'rsvp_date', 'share_link'
    ]
    list_filter = ['rsvp_status', 'event__date']
    search_fields = ['event__title', 'invitee__username', 'invitee__email']
    date_hierarchy = 'created_at'
    
    readonly_fields = ['share_link', 'permission_level']
    
    def permission_level(self, obj):
        return obj.share.permission_type if obj.share else 'No Share'
    permission_level.short_description = 'Permission'
    
    def share_link(self, obj):
        if obj.share:
            url = reverse('admin:shares_share_change', args=[obj.share.id])
            return format_html('<a href="{}">View Share</a>', url)
        return 'No Share'
    share_link.short_description = 'Share'


@admin.register(AgendaComment)
class AgendaCommentAdmin(admin.ModelAdmin):
    list_display = ['agenda_item', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at', 'agenda_item__space__event__date']
    search_fields = ['content', 'author__username', 'agenda_item__title']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
