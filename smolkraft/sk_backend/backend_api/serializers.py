from rest_framework import serializers
from decimal import Decimal
from django.db.models import Sum, Min, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from .models import (
    BOMHeader, BOMLine, BOOHeader, Operation, Material,
    ProductionOrder, Inventory, OrderHeader, OrderLineItem
)

# Basic serializers for reference data
class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'short_name', 'description']

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'sequence_number', 'description', 'estimated_time', 'time_uom']

# ============= BOM SERIALIZERS =============

class BOMLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.short_name', read_only=True)
    material_description = serializers.CharField(source='material.description', read_only=True)

    class Meta:
        model = BOMLine
        fields = ['id', 'material', 'material_name', 'material_description', 'quantity', 'uom']

class BOOHeaderSerializer(serializers.ModelSerializer):
    operations = OperationSerializer(source='operation_set', many=True, read_only=True)

    class Meta:
        model = BOOHeader
        fields = ['id', 'operations']

class BOMDetailSerializer(serializers.ModelSerializer):
    """Complete BOM with all material details and operations"""
    materials = BOMLineSerializer(source='bomline_set', many=True, read_only=True)
    operations = serializers.SerializerMethodField()

    class Meta:
        model = BOMHeader
        fields = ['id', 'product_name', 'description', 'output_quantity',
                  'output_uom', 'materials', 'operations']

    def get_operations(self, obj):
        try:
            boo_header = BOOHeader.objects.get(bom_header=obj)
            operations = Operation.objects.filter(boo_header=boo_header).order_by('sequence_number')
            return OperationSerializer(operations, many=True).data
        except BOOHeader.DoesNotExist:
            return []

# ============= PRODUCTION ORDER SERIALIZERS =============

class ProductionOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='bom_header.product_name', read_only=True)

    class Meta:
        model = ProductionOrder
        fields = ['id', 'bom_header', 'product_name', 'production_date',
                  'quantity', 'status']

class ProductionOrderDetailSerializer(serializers.ModelSerializer):
    """Production Order with BOM details and inventory impacts"""
    product_name = serializers.CharField(source='bom_header.product_name', read_only=True)
    bom_details = serializers.SerializerMethodField()
    inventory_produced = serializers.SerializerMethodField()
    materials_consumed = serializers.SerializerMethodField()

    class Meta:
        model = ProductionOrder
        fields = ['id', 'bom_header', 'product_name', 'production_date',
                  'quantity', 'status', 'bom_details', 'inventory_produced',
                  'materials_consumed']

    def get_bom_details(self, obj):
        return BOMDetailSerializer(obj.bom_header).data

    def get_inventory_produced(self, obj):
        # Get inventory items produced by this production order
        inventory_items = Inventory.objects.filter(production_order=obj)
        return [{'id': item.id, 'material': item.material.short_name,
                 'quantity': item.quantity, 'uom': item.uom}
                for item in inventory_items]

    def get_materials_consumed(self, obj):
        # Calculate materials that would be consumed based on BOM
        bom_lines = BOMLine.objects.filter(bom_header=obj.bom_header)
        consumed = []

        for line in bom_lines:
            # Calculate quantity needed for this production order
            quantity_per_unit = line.quantity
            total_quantity = quantity_per_unit * obj.quantity

            consumed.append({
                'material': line.material.short_name,
                'quantity_needed': total_quantity,
                'uom': line.uom
            })

        return consumed

# ============= INVENTORY SERIALIZERS =============

class InventorySerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.short_name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'material', 'material_name', 'quantity', 'uom', 'location']

# 1. CURRENT INVENTORY SERIALIZER
class LotNumberField(serializers.Field):
    """Custom field for lot number extraction from production order info"""
    def to_representation(self, value):
        if value:
            return f"LOT-{value.id}"
        return None

class ExpirationDateField(serializers.Field):
    """Custom field for expiration date calculation"""
    def to_representation(self, value):
        if value:
            # Assuming expiration is 90 days after production date, adjust as needed
            from datetime import timedelta
            return (value.production_date + timedelta(days=90)).isoformat()
        return None

class CurrentInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='material.short_name', read_only=True)
    lot_number = LotNumberField(source='production_order')
    expiration_date = ExpirationDateField(source='production_order')

    class Meta:
        model = Inventory
        fields = ['id', 'product_name', 'lot_number', 'quantity', 'uom',
                  'expiration_date', 'location']

# 2. INVENTORY SHORTFALL SERIALIZER
class ShortfallSerializer(serializers.Serializer):
    """Serializer for inventory shortfall analysis"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    available_quantity = serializers.DecimalField(max_digits=14, decimal_places=6)
    needed_quantity = serializers.DecimalField(max_digits=14, decimal_places=6)
    shortfall = serializers.DecimalField(max_digits=14, decimal_places=6)
    uom = serializers.CharField()
    oldest_order_date = serializers.DateField(allow_null=True)

    @classmethod
    def get_shortfall_data(cls, user_id):
        """Class method to calculate shortfall data"""
        # Get current inventory levels
        inventory_data = {}
        inventory_items = Inventory.objects.filter(owner_user_id=user_id)

        for item in inventory_items:
            material_id = item.material.id
            if material_id not in inventory_data:
                inventory_data[material_id] = {
                    'product_id': material_id,
                    'product_name': item.material.short_name,
                    'available_quantity': Decimal('0'),
                    'uom': item.uom
                }
            inventory_data[material_id]['available_quantity'] += item.quantity

        # Get needed quantities from open orders
        open_orders = OrderLineItem.objects.filter(
            owner_user_id=user_id,
            order_header__order_date__gte='2024-01-01'  # Filter for recent/active orders
        ).values('material').annotate(
            needed_quantity=Sum('item_count'),
            oldest_date=Min('order_header__order_date')
        )

        # Calculate shortfall
        result = []

        # First, add materials with open orders
        for order in open_orders:
            material_id = order['material']
            needed = order['needed_quantity']

            if material_id in inventory_data:
                available = inventory_data[material_id]['available_quantity']
                inventory_data[material_id]['needed_quantity'] = needed
                inventory_data[material_id]['shortfall'] = max(Decimal('0'), needed - available)
                inventory_data[material_id]['oldest_order_date'] = order['oldest_date']
            else:
                # Material needed but not in inventory
                material = Material.objects.get(id=material_id)
                result.append({
                    'product_id': material_id,
                    'product_name': material.short_name,
                    'available_quantity': Decimal('0'),
                    'needed_quantity': needed,
                    'shortfall': needed,
                    'uom': 'UNIT',  # Default UOM, adjust as needed
                    'oldest_order_date': order['oldest_date']
                })

        # Add inventory items to result
        for item in inventory_data.values():
            if 'needed_quantity' not in item:
                item['needed_quantity'] = Decimal('0')
                item['shortfall'] = Decimal('0')
                item['oldest_order_date'] = None
            result.append(item)

        return result

# 3. PRODUCTION POSSIBILITIES SERIALIZER
class ProductionPossibilitySerializer(serializers.Serializer):
    """Serializer for production possibilities based on available inventory"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    batches_possible = serializers.IntegerField()
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    limiting_component = serializers.CharField(allow_null=True)
    component_materials = serializers.ListField(child=serializers.DictField())

    @classmethod
    def get_production_possibilities(cls, user_id):
        """Class method to calculate production possibilities"""
        # Get all BOMs
        boms = BOMHeader.objects.filter(owner_user_id=user_id)
        result = []

        # Get current inventory levels
        inventory = {}
        for item in Inventory.objects.filter(owner_user_id=user_id):
            if item.material_id not in inventory:
                inventory[item.material_id] = Decimal('0')
            inventory[item.material_id] += item.quantity

        for bom in boms:
            components = []
            min_batches = None
            limiting_component = None
            total_cost = Decimal('0')

            # Check each component
            for line in BOMLine.objects.filter(bom_header=bom):
                material_name = line.material.short_name
                required_per_batch = line.quantity
                available = inventory.get(line.material_id, Decimal('0'))

                # Calculate max batches possible with this component
                if required_per_batch > 0:
                    batches = int(available / required_per_batch)
                else:
                    batches = 9999  # Effectively unlimited

                # Get recent cost data if available
                latest_order = OrderLineItem.objects.filter(
                    material=line.material
                ).order_by('-order_header__order_date').first()

                if latest_order:
                    unit_cost = latest_order.unit_price
                else:
                    unit_cost = Decimal('0')

                component_cost = unit_cost * required_per_batch
                total_cost += component_cost

                components.append({
                    'material_id': line.material_id,
                    'material_name': material_name,
                    'required_per_batch': required_per_batch,
                    'available': available,
                    'max_batches': batches,
                    'unit_cost': unit_cost,
                    'component_cost': component_cost
                })

                # Update min batches possible
                if min_batches is None or batches < min_batches:
                    min_batches = batches
                    limiting_component = material_name

            if min_batches is None:
                min_batches = 0

            result.append({
                'product_id': bom.id,
                'product_name': bom.product_name,
                'batches_possible': min_batches,
                'unit_cost': total_cost,
                'limiting_component': limiting_component,
                'component_materials': components
            })

        return result