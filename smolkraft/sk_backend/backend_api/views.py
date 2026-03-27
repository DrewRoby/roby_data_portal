from rest_framework import viewsets, views, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login

from .models import (
    BOMHeader, BOMLine, BOOHeader, Operation, Material,
    ProductionOrder, Inventory, OrderHeader, OrderLineItem
)
from .serializers import (
    BOMDetailSerializer, ProductionOrderSerializer, ProductionOrderDetailSerializer,
    InventorySerializer, CurrentInventorySerializer, ShortfallSerializer,
    ProductionPossibilitySerializer, MaterialSerializer
)

class LoginView(views.APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return Response({'message': 'Login succful'})
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# Basic viewsets for CRUD operations
class MaterialViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Material.objects.filter(insert_user=self.request.user)

class BOMViewSet(viewsets.ModelViewSet):
    serializer_class = BOMDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BOMHeader.objects.filter(owner_user_id=self.request.user)

class ProductionOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductionOrder.objects.filter(owner_user_id=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Override to use detailed serializer for single item view"""
        instance = self.get_object()
        serializer = ProductionOrderDetailSerializer(instance)
        return Response(serializer.data)

class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inventory.objects.filter(owner_user_id=self.request.user)

# Specialized views for complex data requirements
class CurrentInventoryView(views.APIView):
    """View for current inventory with lot numbers and expiration dates"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        inventory = Inventory.objects.filter(
            owner_user_id=request.user
        ).select_related('material', 'production_order')

        serializer = CurrentInventorySerializer(inventory, many=True)
        return Response(serializer.data)

class InventoryShortfallView(views.APIView):
    """View for inventory shortfall analysis"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        shortfall_data = ShortfallSerializer.get_shortfall_data(request.user.id)
        serializer = ShortfallSerializer(shortfall_data, many=True)
        return Response(serializer.data)

class ProductionPossibilitiesView(views.APIView):
    """View for production possibilities based on available inventory"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        possibilities = ProductionPossibilitySerializer.get_production_possibilities(request.user.id)
        serializer = ProductionPossibilitySerializer(possibilities, many=True)
        return Response(serializer.data)