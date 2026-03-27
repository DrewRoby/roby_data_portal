# backend_api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend_api.views import (
    MaterialViewSet,
    BOMViewSet,
    ProductionOrderViewSet,
    InventoryViewSet,
    CurrentInventoryView,
    InventoryShortfallView,
    ProductionPossibilitiesView,
)

app_name = 'backend_api'

router = DefaultRouter()
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'boms', BOMViewSet, basename='bom')
router.register(r'production-orders', ProductionOrderViewSet, basename='production-order')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/current-inventory/', CurrentInventoryView.as_view(), name='current-inventory'),
    path('api/inventory-shortfall/', InventoryShortfallView.as_view(), name='inventory-shortfall'),
    path('api/production-possibilities/', ProductionPossibilitiesView.as_view(), name='production-possibilities'),
    # obtain_auth_token removed — portal session auth handles all authentication
    # LoginView removed — same reason
]