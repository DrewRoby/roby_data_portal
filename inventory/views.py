# inventory/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Warehouse, Rack, Shelf, Bin, Item
from .serializers import (
    WarehouseSerializer, RackSerializer, ShelfSerializer, 
    BinSerializer, ItemSerializer
)

# Base class for list and create operations
class BaseListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter objects by the authenticated user."""
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Save the object with the current user."""
        serializer.save(user=self.request.user)

# Base class for retrieve, update, and delete operations
class BaseRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter objects by the authenticated user."""
        return self.queryset.filter(user=self.request.user)

# Warehouse views
class WarehouseListCreateView(BaseListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

class WarehouseDetailView(BaseRetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

# Rack views
class RackListCreateView(generics.ListCreateAPIView):
    serializer_class = RackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=self.request.user)
        return Rack.objects.filter(warehouse=warehouse)
    
    def perform_create(self, serializer):
        warehouse_id = self.kwargs.get('warehouse_id')
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=self.request.user)
        serializer.save(warehouse=warehouse)

class RackDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=self.request.user)
        return Rack.objects.filter(warehouse=warehouse)

# Shelf views - follow the same pattern as Rack
class ShelfListCreateView(generics.ListCreateAPIView):
    serializer_class = ShelfSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        rack = get_object_or_404(
            Rack, 
            id=rack_id, 
            warehouse__id=warehouse_id,
            warehouse__user=self.request.user
        )
        return Shelf.objects.filter(rack=rack)
    
    def perform_create(self, serializer):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        rack = get_object_or_404(
            Rack, 
            id=rack_id, 
            warehouse__id=warehouse_id,
            warehouse__user=self.request.user
        )
        serializer.save(rack=rack)

class ShelfDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShelfSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        rack = get_object_or_404(
            Rack, 
            id=rack_id, 
            warehouse__id=warehouse_id,
            warehouse__user=self.request.user
        )
        return Shelf.objects.filter(rack=rack)

# Bin views - follow the same pattern as Shelf
class BinListCreateView(generics.ListCreateAPIView):
    serializer_class = BinSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        shelf = get_object_or_404(
            Shelf, 
            id=shelf_id, 
            rack__id=rack_id,
            rack__warehouse__id=warehouse_id,
            rack__warehouse__user=self.request.user
        )
        return Bin.objects.filter(shelf=shelf)
    
    def perform_create(self, serializer):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        shelf = get_object_or_404(
            Shelf, 
            id=shelf_id, 
            rack__id=rack_id,
            rack__warehouse__id=warehouse_id,
            rack__warehouse__user=self.request.user
        )
        serializer.save(shelf=shelf)

class BinDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BinSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        shelf = get_object_or_404(
            Shelf, 
            id=shelf_id, 
            rack__id=rack_id,
            rack__warehouse__id=warehouse_id,
            rack__warehouse__user=self.request.user
        )
        return Bin.objects.filter(shelf=shelf)

# Item views - follow the same pattern as Bin
class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        bin_id = self.kwargs.get('bin_id')
        bin_obj = get_object_or_404(
            Bin, 
            id=bin_id, 
            shelf__id=shelf_id,
            shelf__rack__id=rack_id,
            shelf__rack__warehouse__id=warehouse_id,
            shelf__rack__warehouse__user=self.request.user
        )
        return Item.objects.filter(bin=bin_obj)
    
    def perform_create(self, serializer):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        bin_id = self.kwargs.get('bin_id')
        bin_obj = get_object_or_404(
            Bin, 
            id=bin_id, 
            shelf__id=shelf_id,
            shelf__rack__id=rack_id,
            shelf__rack__warehouse__id=warehouse_id,
            shelf__rack__warehouse__user=self.request.user
        )
        serializer.save(bin=bin_obj)

class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        rack_id = self.kwargs.get('rack_id')
        shelf_id = self.kwargs.get('shelf_id')
        bin_id = self.kwargs.get('bin_id')
        bin_obj = get_object_or_404(
            Bin, 
            id=bin_id, 
            shelf__id=shelf_id,
            shelf__rack__id=rack_id,
            shelf__rack__warehouse__id=warehouse_id,
            shelf__rack__warehouse__user=self.request.user
        )
        return Item.objects.filter(bin=bin_obj)