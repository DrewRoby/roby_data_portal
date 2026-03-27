from django.contrib import admin
from .models import (
    Material, BOMHeader, BOMLine, BOOHeader, Operation,
    ProductionOrder, Inventory, OrderHeader, OrderLineItem,
    Vendor, UnitConversion
)

# Inline model configurations
class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 1
    autocomplete_fields = ['material']

class OperationInline(admin.TabularInline):
    model = Operation
    extra = 1
    fields = ['sequence_number', 'description', 'estimated_time', 'time_uom']

class OrderLineItemInline(admin.TabularInline):
    model = OrderLineItem
    extra = 1
    autocomplete_fields = ['material']

# Main model admin classes
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'description', 'bom_header']
    search_fields = ['short_name', 'description']
    list_filter = ['bom_header__product_name']
    autocomplete_fields = ['bom_header']

@admin.register(BOMHeader)
class BOMHeaderAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'description', 'output_quantity', 'output_uom']
    search_fields = ['product_name', 'description']
    inlines = [BOMLineInline]

@admin.register(BOOHeader)
class BOOHeaderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'bom_header']
    autocomplete_fields = ['bom_header']
    inlines = [OperationInline]

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'production_date', 'quantity', 'status']
    list_filter = ['status', 'production_date']
    search_fields = ['production_order']
    autocomplete_fields = ['bom_header']
    date_hierarchy = 'production_date'

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['material', 'quantity', 'uom', 'location', 'production_order']
    list_filter = ['uom', 'location', 'material']
    search_fields = ['material__short_name', 'location']
    autocomplete_fields = ['material', 'production_order']

@admin.register(OrderHeader)
class OrderHeaderAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'order_date', 'cost_total', 'item_count']
    list_filter = ['vendor', 'order_date']
    date_hierarchy = 'order_date'
    inlines = [OrderLineItemInline]

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['vendor_name']
    search_fields = ['vendor_name']

@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ['from_unit_name', 'to_unit_name', 'multiply_by']
    search_fields = ['from_unit_name', 'to_unit_name']