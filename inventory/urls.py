# inventory/urls.py
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Warehouse URLs
    path('warehouses/', views.warehouse_list, name='warehouse-list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse-create'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse-detail'),
    path('warehouses/<int:warehouse_id>/update/', views.warehouse_update, name='warehouse-update'),
    path('warehouses/<int:warehouse_id>/delete/', views.warehouse_delete, name='warehouse-delete'),
    
    # Rack URLs
    path('warehouses/<int:warehouse_id>/racks/create/', views.rack_create, name='rack-create'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/', views.rack_detail, name='rack-detail'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/update/', views.rack_update, name='rack-update'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/delete/', views.rack_delete, name='rack-delete'),
    
    # Shelf URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/create/', 
         views.shelf_create, name='shelf-create'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/', 
         views.shelf_detail, name='shelf-detail'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/update/', 
         views.shelf_update, name='shelf-update'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/delete/', 
         views.shelf_delete, name='shelf-delete'),
    
    # Bin URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/create/', 
         views.bin_create, name='bin-create'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/', 
         views.bin_detail, name='bin-detail'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/update/', 
         views.bin_update, name='bin-update'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/delete/', 
         views.bin_delete, name='bin-delete'),
    
    # Item URLs
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/create/', 
         views.item_create, name='item-create'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/', 
         views.item_detail, name='item-detail'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/update/', 
         views.item_update, name='item-update'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/delete/', 
         views.item_delete, name='item-delete'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/transfer/', 
         views.item_transfer, name='item-transfer'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/disposition/', 
         views.item_disposition, name='item-disposition'),
    path('warehouses/<int:warehouse_id>/racks/<int:rack_id>/shelves/<int:shelf_id>/bins/<int:bin_id>/items/<int:item_id>/add-stock/', 
     views.item_add_stock, name='item-add-stock'),
    
    # Utility URLs
    path('search/', views.search, name='search'),
    path('low-stock/', views.low_stock, name='low-stock'),
    path('restock-item/', views.restock_item, name='restock-item'),
    path('report/', views.report, name='report'),
    path('export/low-stock/', views.export_low_stock, name='export-low-stock'),
]