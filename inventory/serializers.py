from rest_framework import serializers
from .models import Warehouse, Rack, Shelf, Bin, Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'quantity', 'sku', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class BinSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Bin
        fields = ['id', 'name', 'description', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ShelfSerializer(serializers.ModelSerializer):
    bins = BinSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shelf
        fields = ['id', 'name', 'description', 'bins', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class RackSerializer(serializers.ModelSerializer):
    shelves = ShelfSerializer(many=True, read_only=True)
    
    class Meta:
        model = Rack
        fields = ['id', 'name', 'description', 'shelves', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class WarehouseSerializer(serializers.ModelSerializer):
    racks = RackSerializer(many=True, read_only=True)
    
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'description', 'racks', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']