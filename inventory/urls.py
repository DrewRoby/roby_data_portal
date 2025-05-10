from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Warehouse URLs
    path('warehouses/', views.WarehouseListCreateView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    
    # Rack URLs
    path('warehouses/<int:warehouse_id>/racks/', views.RackListCreateView.as_view(), name='rack-list'),
    path('warehouses/<int:warehouse_id>/racks/<int:pk>/', views.RackDetailView.as_view(), name='rack-detail'),
    
    # Shelf URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/', 
        views.ShelfListCreateView.as_view(), name='shelf-list'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:pk>/', 
        views.ShelfDetailView.as_view(), name='shelf-detail'),
    
    # Bin URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/', 
        views.BinListCreateView.as_view(), name='bin-list'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:pk>/', 
        views.BinDetailView.as_view(), name='bin-detail'),
    
    # Item URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/', 
        views.ItemListCreateView.as_view(), name='item-list'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:pk>/', 
        views.ItemDetailView.as_view(), name='item-detail'),
]