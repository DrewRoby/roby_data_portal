from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend_api.views import (
    MaterialViewSet, BOMViewSet, ProductionOrderViewSet, InventoryViewSet,
    CurrentInventoryView, InventoryShortfallView, ProductionPossibilitiesView,
    LoginView
)
from rest_framework.authtoken.views import obtain_auth_token


router = DefaultRouter()
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'boms', BOMViewSet, basename='bom')
router.register(r'production-orders', ProductionOrderViewSet, basename='production-order')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    # Router URLs for standard CRUD endpoints
    path('api/', include(router.urls)),

    # Specialized report endpoints
    path('api/current-inventory/', CurrentInventoryView.as_view(), name='current-inventory'),
    path('api/inventory-shortfall/', InventoryShortfallView.as_view(), name='inventory-shortfall'),
    path('api/production-possibilities/', ProductionPossibilitiesView.as_view(), name='production-possibilities'),
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
    # path('api/login/', LoginView.as_view(), name='api_login'),
]