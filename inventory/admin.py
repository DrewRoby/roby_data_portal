from django.contrib import admin
from .models import Warehouse, Rack, Shelf, Bin, Item, Disposition, StockAddition

class StockAdditionAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'addition_type', 'timestamp', 'created_by')
    list_filter = ('addition_type', 'timestamp')
    search_fields = ('item__name', 'notes')
    date_hierarchy = 'timestamp'

admin.site.register(StockAddition, StockAdditionAdmin)