from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from smolkraft.sk_backend.backend_api.views import (
    MaterialViewSet,
    BOMViewSet,
    ProductionOrderViewSet,
    InventoryViewSet,
    CurrentInventoryView,
    InventoryShortfallView,
    ProductionPossibilitiesView,
    SmolkraftAppView,
)

app_name = 'smolkraft'

router = DefaultRouter()
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'boms', BOMViewSet, basename='bom')
router.register(r'production-orders', ProductionOrderViewSet, basename='production-order')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    # REST API — must come before the catch-all
    path('api/', include(router.urls)),
    path('api/current-inventory/', CurrentInventoryView.as_view(), name='current-inventory'),
    path('api/inventory-shortfall/', InventoryShortfallView.as_view(), name='inventory-shortfall'),
    path('api/production-possibilities/', ProductionPossibilitiesView.as_view(), name='production-possibilities'),

    # Vue SPA — catches /, /materials/, /boms/, etc. for client-side routing
    re_path(r'^(?!api/).*$', SmolkraftAppView.as_view(), name='app'),
]
