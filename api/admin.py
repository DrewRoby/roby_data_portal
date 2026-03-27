from django.contrib import admin
from .models import APIUsageLog

@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'timestamp', 'response_count', 'success')
    list_filter = ('endpoint', 'success', 'timestamp')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')