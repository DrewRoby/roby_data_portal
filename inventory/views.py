# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
import csv
import json

from .models import Warehouse, Rack, Shelf, Bin, Item, StockAddition, Disposition
from .forms import (
    WarehouseForm, RackForm, ShelfForm, BinForm, ItemForm,
    ItemTransferForm, RestockForm, SearchForm, DispositionForm,
    StockAdditionForm
)

# Dashboard
def dashboard(request):
    """
    Display the inventory dashboard with key metrics and recent activity.
    """
    warehouse_count = Warehouse.objects.filter(user=request.user).count()
    
    item_count = Item.objects.filter(
        bin__shelf__rack__warehouse__user=request.user
    ).count()
    
    total_quantity = Item.objects.filter(
        bin__shelf__rack__warehouse__user=request.user
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Define what "low stock" means - items with quantity < 5 for this example
    low_stock_count = Item.objects.filter(
        bin__shelf__rack__warehouse__user=request.user,
        quantity__lt=5
    ).count()
    
    # Get recent activities (this would be from a hypothetical ActivityLog model)
    # We'll mock this for the example
    recent_activities = [
        {
            'item_name': 'Example Item',
            'location': 'Warehouse A > Rack 1 > Shelf 2 > Bin 3',
            'action': 'Updated quantity',
            'timestamp': timezone.now(),
            'detail_url': '#'
        }
    ]
    
    recent_activity_count = len(recent_activities)
    
    context = {
        'warehouse_count': warehouse_count,
        'item_count': item_count,
        'total_quantity': total_quantity,
        'low_stock_count': low_stock_count,
        'recent_activities': recent_activities,
        'recent_activity_count': recent_activity_count,
    }
    
    return render(request, 'inventory/dashboard.html', context)

# Warehouse Views
def warehouse_list(request):
    """
    Display a list of all warehouses belonging to the user.
    """
    warehouses = Warehouse.objects.filter(user=request.user).order_by('name')
    
    context = {
        'warehouses': warehouses
    }
    
    return render(request, 'inventory/warehouse_list.html', context)

def warehouse_detail(request, warehouse_id):
    """
    Display details of a specific warehouse.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    
    # Count all items, shelves and bins in this warehouse
    shelves_count = Shelf.objects.filter(rack__warehouse=warehouse).count()
    bins_count = Bin.objects.filter(shelf__rack__warehouse=warehouse).count()
    items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
    
    context = {
        'warehouse': warehouse,
        'shelves_count': shelves_count,
        'bins_count': bins_count,
        'items_count': items_count
    }
    
    return render(request, 'inventory/warehouse_detail.html', context)

def warehouse_create(request):
    """
    Create a new warehouse.
    """
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.user = request.user
            warehouse.save()
            
            messages.success(request, f'Warehouse "{warehouse.name}" has been created.')
            return redirect('inventory:warehouse-detail', warehouse_id=warehouse.id)
    else:
        form = WarehouseForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'inventory/warehouse_form.html', context)

def warehouse_update(request, warehouse_id):
    """
    Update an existing warehouse.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Warehouse "{warehouse.name}" has been updated.')
            return redirect('inventory:warehouse-detail', warehouse_id=warehouse.id)
    else:
        form = WarehouseForm(instance=warehouse)
    
    context = {
        'form': form,
        'warehouse': warehouse
    }
    
    return render(request, 'inventory/warehouse_form.html', context)

def warehouse_delete(request, warehouse_id):
    """
    Delete a warehouse.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    
    # Count all shelves, bins and items in this warehouse for the confirmation page
    shelves_count = Shelf.objects.filter(rack__warehouse=warehouse).count()
    bins_count = Bin.objects.filter(shelf__rack__warehouse=warehouse).count()
    items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
    
    if request.method == 'POST':
        warehouse_name = warehouse.name
        warehouse.delete()
        
        messages.success(request, f'Warehouse "{warehouse_name}" has been deleted.')
        return redirect('inventory:warehouse-list')
    
    context = {
        'warehouse': warehouse,
        'shelves_count': shelves_count,
        'bins_count': bins_count,
        'items_count': items_count
    }
    
    return render(request, 'inventory/warehouse_confirm_delete.html', context)

# Rack Views
def rack_detail(request, warehouse_id, rack_id):
    """
    Display details of a specific rack.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    
    # Count all bins and items in this rack
    bins_count = Bin.objects.filter(shelf__rack=rack).count()
    items_count = Item.objects.filter(bin__shelf__rack=rack).count()
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'bins_count': bins_count,
        'items_count': items_count
    }
    
    return render(request, 'inventory/rack_detail.html', context)

def rack_create(request, warehouse_id):
    """
    Create a new rack within a warehouse.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    
    if request.method == 'POST':
        form = RackForm(request.POST)
        if form.is_valid():
            rack = form.save(commit=False)
            rack.warehouse = warehouse
            rack.save()
            
            messages.success(request, f'Rack "{rack.name}" has been created.')
            return redirect('inventory:rack-detail', warehouse_id=warehouse.id, rack_id=rack.id)
    else:
        form = RackForm()
    
    context = {
        'form': form,
        'warehouse': warehouse
    }
    
    return render(request, 'inventory/rack_form.html', context)

def rack_update(request, warehouse_id, rack_id):
    """
    Update an existing rack.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    
    if request.method == 'POST':
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Rack "{rack.name}" has been updated.')
            return redirect('inventory:rack-detail', warehouse_id=warehouse.id, rack_id=rack.id)
    else:
        form = RackForm(instance=rack)
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack
    }
    
    return render(request, 'inventory/rack_form.html', context)

def rack_delete(request, warehouse_id, rack_id):
    """
    Delete a rack.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    
    # Count bins and items for confirmation page
    bins_count = Bin.objects.filter(shelf__rack=rack).count()
    items_count = Item.objects.filter(bin__shelf__rack=rack).count()
    
    if request.method == 'POST':
        rack_name = rack.name
        rack.delete()
        
        messages.success(request, f'Rack "{rack_name}" has been deleted.')
        return redirect('inventory:warehouse-detail', warehouse_id=warehouse.id)
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'bins_count': bins_count,
        'items_count': items_count
    }
    
    return render(request, 'inventory/rack_confirm_delete.html', context)

# Shelf Views
def shelf_detail(request, warehouse_id, rack_id, shelf_id):
    """
    Display details of a specific shelf.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    
    # Count all items in this shelf
    items_count = Item.objects.filter(bin__shelf=shelf).count()
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'items_count': items_count
    }
    
    return render(request, 'inventory/shelf_detail.html', context)

def shelf_create(request, warehouse_id, rack_id):
    """
    Create a new shelf within a rack.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST)
        if form.is_valid():
            shelf = form.save(commit=False)
            shelf.rack = rack
            shelf.save()
            
            messages.success(request, f'Shelf "{shelf.name}" has been created.')
            return redirect('inventory:shelf-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id)
    else:
        form = ShelfForm()
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack
    }
    
    return render(request, 'inventory/shelf_form.html', context)

def shelf_update(request, warehouse_id, rack_id, shelf_id):
    """
    Update an existing shelf.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST, instance=shelf)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Shelf "{shelf.name}" has been updated.')
            return redirect('inventory:shelf-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id)
    else:
        form = ShelfForm(instance=shelf)
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf
    }
    
    return render(request, 'inventory/shelf_form.html', context)

def shelf_delete(request, warehouse_id, rack_id, shelf_id):
    """
    Delete a shelf.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    
    # Count items for confirmation page
    items_count = Item.objects.filter(bin__shelf=shelf).count()
    
    if request.method == 'POST':
        shelf_name = shelf.name
        shelf.delete()
        
        messages.success(request, f'Shelf "{shelf_name}" has been deleted.')
        return redirect('inventory:rack-detail', warehouse_id=warehouse.id, rack_id=rack.id)
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'items_count': items_count
    }
    
    return render(request, 'inventory/shelf_confirm_delete.html', context)

# Bin Views
def bin_detail(request, warehouse_id, rack_id, shelf_id, bin_id):
    """
    Display details of a specific bin.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    
    # Calculate total quantity of all items in this bin
    total_quantity = Item.objects.filter(bin=bin_obj).aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'total_quantity': total_quantity
    }
    
    return render(request, 'inventory/bin_detail.html', context)

def bin_create(request, warehouse_id, rack_id, shelf_id):
    """
    Create a new bin within a shelf.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    
    if request.method == 'POST':
        form = BinForm(request.POST)
        if form.is_valid():
            bin_obj = form.save(commit=False)
            bin_obj.shelf = shelf
            bin_obj.save()
            
            messages.success(request, f'Bin "{bin_obj.name}" has been created.')
            return redirect('inventory:bin-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id,
                           bin_id=bin_obj.id)
    else:
        form = BinForm()
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf
    }
    
    return render(request, 'inventory/bin_form.html', context)

def bin_update(request, warehouse_id, rack_id, shelf_id, bin_id):
    """
    Update an existing bin.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    
    if request.method == 'POST':
        form = BinForm(request.POST, instance=bin_obj)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Bin "{bin_obj.name}" has been updated.')
            return redirect('inventory:bin-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id,
                           bin_id=bin_obj.id)
    else:
        form = BinForm(instance=bin_obj)
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj
    }
    
    return render(request, 'inventory/bin_form.html', context)

def bin_delete(request, warehouse_id, rack_id, shelf_id, bin_id):
    """
    Delete a bin.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    
    # Get total quantity for confirmation page
    total_quantity = Item.objects.filter(bin=bin_obj).aggregate(total=Sum('quantity'))['total'] or 0
    
    if request.method == 'POST':
        bin_name = bin_obj.name
        bin_obj.delete()
        
        messages.success(request, f'Bin "{bin_name}" has been deleted.')
        return redirect('inventory:shelf-detail', 
                       warehouse_id=warehouse.id, 
                       rack_id=rack.id,
                       shelf_id=shelf.id)
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'total_quantity': total_quantity
    }
    
    return render(request, 'inventory/bin_confirm_delete.html', context)

# Item Views
# inventory/views.py
def item_detail(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Display details of a specific item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    # Get activity history ordered by timestamp
    dispositions = item.dispositions.all().order_by('-timestamp')
    additions = item.additions.all().order_by('-timestamp')
    
    # Create combined history list for the template
    # We'll create a list of dicts with a uniform structure for easier template rendering
    history_items = []
    
    for disposition in dispositions:
        history_items.append({
            'timestamp': disposition.timestamp,
            'type': 'disposition',
            'quantity': -disposition.quantity,  # Negative for dispositions
            'reason': disposition.get_disposition_type_display(),
            'notes': disposition.notes,
            'user': disposition.created_by.username
        })
    
    for addition in additions:
        history_items.append({
            'timestamp': addition.timestamp,
            'type': 'addition',
            'quantity': addition.quantity,  # Positive for additions
            'reason': addition.get_addition_type_display(),
            'notes': addition.notes,
            'user': addition.created_by.username
        })
    
    # Sort by timestamp (most recent first)
    history_items.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item,
        'history_items': history_items
    }
    
    return render(request, 'inventory/item_detail.html', context)

def item_create(request, warehouse_id, rack_id, shelf_id, bin_id):
    """
    Create a new item within a bin.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.bin = bin_obj
            item.save()
            
            # Check if we should redirect to add another item
            add_another = request.POST.get('add_another') == '1'
            
            messages.success(request, f'Item "{item.name}" has been created.')
            
            if add_another:
                # Redirect back to the create form
                return redirect('inventory:item-create', 
                              warehouse_id=warehouse.id, 
                              rack_id=rack.id,
                              shelf_id=shelf.id,
                              bin_id=bin_obj.id)
            else:
                # Redirect to the item detail page
                return redirect('inventory:bin-detail', 
                              warehouse_id=warehouse.id, 
                              rack_id=rack.id,
                              shelf_id=shelf.id,
                              bin_id=bin_obj.id)
    else:
        form = ItemForm()
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj
    }
    
    return render(request, 'inventory/item_form.html', context)
def item_update(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Update an existing item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Item "{item.name}" has been updated.')
            return redirect('inventory:item-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id,
                           bin_id=bin_obj.id,
                           item_id=item.id)
    else:
        form = ItemForm(instance=item)
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item
    }
    
    return render(request, 'inventory/item_form.html', context)

def item_delete(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Delete an item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        
        messages.success(request, f'Item "{item_name}" has been deleted.')
        return redirect('inventory:bin-detail', 
                       warehouse_id=warehouse.id, 
                       rack_id=rack.id,
                       shelf_id=shelf.id,
                       bin_id=bin_obj.id)
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item
    }
    
    return render(request, 'inventory/item_confirm_delete.html', context)

def item_transfer(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Transfer an item to a different bin location.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    # Get all available warehouses, racks, shelves and bins for dropdown selection
    warehouses = Warehouse.objects.filter(user=request.user)
    racks = Rack.objects.filter(warehouse=warehouse)
    shelves = Shelf.objects.filter(rack=rack)
    bins = Bin.objects.filter(shelf=shelf)
    
    if request.method == 'POST':
        form = ItemTransferForm(request.POST, user=request.user)
        if form.is_valid():
            # Get the new bin
            new_warehouse_id = form.cleaned_data['warehouse']
            new_rack_id = form.cleaned_data['rack']
            new_shelf_id = form.cleaned_data['shelf']
            new_bin_id = form.cleaned_data['bin']
            transfer_quantity = form.cleaned_data['quantity']
            
            # Get the destination bin
            new_bin = get_object_or_404(
                Bin, 
                id=new_bin_id, 
                shelf__id=new_shelf_id,
                shelf__rack__id=new_rack_id,
                shelf__rack__warehouse__id=new_warehouse_id,
                shelf__rack__warehouse__user=request.user
            )
            
            # Check if we're transferring all or part of the quantity
            if transfer_quantity >= item.quantity:
                # Transfer the entire item
                item.bin = new_bin
                item.save()
                messages.success(request, f'Item "{item.name}" has been transferred.')
                
                # Redirect to the new location
                return redirect('inventory:item-detail', 
                               warehouse_id=new_warehouse_id, 
                               rack_id=new_rack_id,
                               shelf_id=new_shelf_id,
                               bin_id=new_bin_id,
                               item_id=item.id)
            else:
                # Transfer part of the quantity - create a new item in the destination
                new_item = Item(
                    name=item.name,
                    description=item.description,
                    bin=new_bin,
                    quantity=transfer_quantity,
                    sku=item.sku
                )
                new_item.save()
                
                # Update the original item's quantity
                item.quantity -= transfer_quantity
                item.save()
                
                messages.success(request, f'{transfer_quantity} units of "{item.name}" have been transferred.')
                
                # Redirect to the new item
                return redirect('inventory:item-detail', 
                               warehouse_id=new_warehouse_id, 
                               rack_id=new_rack_id,
                               shelf_id=new_shelf_id,
                               bin_id=new_bin_id,
                               item_id=new_item.id)
    else:
        form = ItemTransferForm(
            user=request.user,
            initial={
                'warehouse': warehouse.id,
                'rack': rack.id,
                'shelf': shelf.id,
                'bin': bin_obj.id,
                'quantity': item.quantity
            }
        )
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item,
        'warehouses': warehouses,
        'racks': racks,
        'shelves': shelves,
        'bins': bins
    }
    
    return render(request, 'inventory/item_transfer.html', context)


# Utility Views
def search(request):
    """
    Search for inventory items.
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    
    if query:
        # Perform search based on the selected type
        if search_type == 'warehouse' or search_type == 'all':
            warehouses = Warehouse.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                user=request.user
            )
        else:
            warehouses = Warehouse.objects.none()
            
        if search_type == 'rack' or search_type == 'all':
            racks = Rack.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                warehouse__user=request.user
            )
        else:
            racks = Rack.objects.none()
            
        if search_type == 'shelf' or search_type == 'all':
            shelves = Shelf.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                rack__warehouse__user=request.user
            )
        else:
            shelves = Shelf.objects.none()
            
        if search_type == 'bin' or search_type == 'all':
            bins = Bin.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                shelf__rack__warehouse__user=request.user
            )
        else:
            bins = Bin.objects.none()
            
        if search_type == 'item' or search_type == 'all':
            items = Item.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) | 
                Q(sku__icontains=query),
                bin__shelf__rack__warehouse__user=request.user
            )
        else:
            items = Item.objects.none()
            
        # Calculate total results
        results_count = warehouses.count() + racks.count() + shelves.count() + bins.count() + items.count()
        
        context = {
            'query': query,
            'type': search_type,
            'warehouses': warehouses,
            'racks': racks,
            'shelves': shelves,
            'bins': bins,
            'items': items,
            'results_count': results_count
        }
        
        return render(request, 'inventory/search_results.html', context)
    else:
        # If no query, show the search form
        return render(request, 'inventory/search.html')

def low_stock(request):
    """
    Display items with low stock levels.
    """
    # Define what "low stock" means - items with quantity < 5 for this example
    # In a real application, this could be a configurable threshold or defined per item
    low_stock_items = Item.objects.filter(
        bin__shelf__rack__warehouse__user=request.user,
        quantity__lt=5
    ).order_by('quantity')
    
    context = {
        'low_stock_items': low_stock_items
    }
    
    return render(request, 'inventory/low_stock.html', context)

def restock_item(request):
    """
    Process the restock form submission.
    """
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']
            
            # Find the item
            try:
                item = Item.objects.get(
                    id=item_id,
                    bin__shelf__rack__warehouse__user=request.user
                )
                
                # Update quantity
                old_quantity = item.quantity
                item.quantity += quantity
                item.save()
                
                messages.success(
                    request, 
                    f'Successfully restocked "{item.name}". Quantity increased from {old_quantity} to {item.quantity}.'
                )
                
                # Get the item's location for the redirect
                bin_obj = item.bin
                shelf = bin_obj.shelf
                rack = shelf.rack
                warehouse = rack.warehouse
                
                return redirect('inventory:item-detail', 
                               warehouse_id=warehouse.id, 
                               rack_id=rack.id,
                               shelf_id=shelf.id,
                               bin_id=bin_obj.id,
                               item_id=item.id)
                               
            except Item.DoesNotExist:
                messages.error(request, 'Item not found.')
                return redirect('inventory:low-stock')
    
    # If not POST or form invalid, redirect to low stock page
    return redirect('inventory:low-stock')

# Enhanced inventory/views.py report function

def report(request):
    """
    Generate enhanced inventory reports with better aggregation and filtering.
    """
    report_type = request.GET.get('report_type')
    warehouse_id = request.GET.get('warehouse')
    timeframe = request.GET.get('timeframe', 'all')  # New parameter for time filtering
    low_stock_threshold = request.GET.get('threshold', 5)  # New parameter for low stock threshold
    sort_by = request.GET.get('sort_by', 'name')  # New parameter for sorting
    
    try:
        low_stock_threshold = int(low_stock_threshold)
    except (ValueError, TypeError):
        low_stock_threshold = 5
    
    # Get all warehouses for the form
    warehouses = Warehouse.objects.filter(user=request.user)
    
    # Set default values
    report_title = "Inventory Report"
    generation_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Variables for report data
    total_items = 0
    total_quantity = 0
    total_bins = 0
    warehouse_data = []
    top_items = []
    low_stock_items = []
    low_stock_count = 0
    warehouse_capacity = []
    warehouse_stats = []
    category_distribution = []
    warehouse_distribution = []
    item_age_distribution = []
    recent_activity = []
    inventory_value = 0
    movement_data = []
    
    # Process based on report type
    if report_type == 'inventory_summary':
        report_title = "Inventory Summary Report"
        
        # Filter by warehouse if specified
        if warehouse_id and warehouse_id != 'all':
            warehouses_to_include = warehouses.filter(id=warehouse_id)
        else:
            warehouses_to_include = warehouses
        
        # Get overall stats
        items_query = Item.objects.filter(bin__shelf__rack__warehouse__in=warehouses_to_include)
        total_items = items_query.count()
        total_quantity = items_query.aggregate(total=Sum('quantity'))['total'] or 0
        total_bins = Bin.objects.filter(shelf__rack__warehouse__in=warehouses_to_include).count()
        
        # Apply time filter if specified
        if timeframe != 'all':
            time_threshold = timezone.now()
            if timeframe == 'day':
                time_threshold = time_threshold - timezone.timedelta(days=1)
            elif timeframe == 'week':
                time_threshold = time_threshold - timezone.timedelta(weeks=1)
            elif timeframe == 'month':
                time_threshold = time_threshold - timezone.timedelta(days=30)
            elif timeframe == 'quarter':
                time_threshold = time_threshold - timezone.timedelta(days=90)
            
            # Filter for recently updated items
            items_query = items_query.filter(updated_at__gte=time_threshold)
            
            # Recalculate totals with time filter
            total_items = items_query.count()
            total_quantity = items_query.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get warehouse-specific data with more metrics
        for warehouse in warehouses_to_include:
            racks_count = Rack.objects.filter(warehouse=warehouse).count()
            shelves_count = Shelf.objects.filter(rack__warehouse=warehouse).count()
            bins_count = Bin.objects.filter(shelf__rack__warehouse=warehouse).count()
            items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
            items_quantity = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).aggregate(
                total=Sum('quantity'))['total'] or 0
            
            # Calculate bins utilization
            bins_with_items = Bin.objects.filter(
                shelf__rack__warehouse=warehouse,
                items__isnull=False
            ).distinct().count()
            
            bins_utilization = 0
            if bins_count > 0:
                bins_utilization = (bins_with_items / bins_count) * 100
            
            # Get item stats - like average items per bin
            avg_items_per_bin = 0
            if bins_with_items > 0:
                avg_items_per_bin = items_count / bins_with_items
            
            # Add enhanced warehouse data
            warehouse_data.append({
                'id': warehouse.id,
                'name': warehouse.name,
                'items': items_count,
                'quantity': items_quantity,
                'racks': racks_count,
                'shelves': shelves_count,
                'bins': bins_count,
                'bins_with_items': bins_with_items,
                'bins_utilization': round(bins_utilization, 1),
                'avg_items_per_bin': round(avg_items_per_bin, 1),
                'last_updated': warehouse.updated_at
            })
        
        # Sort warehouse data
        if sort_by == 'quantity':
            warehouse_data = sorted(warehouse_data, key=lambda x: x['quantity'], reverse=True)
        elif sort_by == 'items':
            warehouse_data = sorted(warehouse_data, key=lambda x: x['items'], reverse=True)
        elif sort_by == 'utilization':
            warehouse_data = sorted(warehouse_data, key=lambda x: x['bins_utilization'], reverse=True)
        else:  # default to name
            warehouse_data = sorted(warehouse_data, key=lambda x: x['name'])
        
        # Get top stocked items with enhanced details
        top_items_query = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include
        ).order_by('-quantity')[:10]
        
        # Format top items for display with more details
        for item in top_items_query:
            bin_obj = item.bin
            shelf = bin_obj.shelf
            rack = shelf.rack
            warehouse = rack.warehouse
            
            # Calculate how long the item has been in stock
            days_in_stock = (timezone.now() - item.created_at).days
            
            top_items.append({
                'id': item.id,
                'name': item.name,
                'sku': item.sku or 'N/A',
                'quantity': item.quantity,
                'days_in_stock': days_in_stock,
                'warehouse': warehouse.name,
                'location': f"{warehouse.name} > {rack.name} > {shelf.name} > {bin_obj.name}",
                'location_url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': warehouse.id,
                    'rack_id': rack.id,
                    'shelf_id': shelf.id,
                    'bin_id': bin_obj.id,
                    'item_id': item.id
                })
            })
        
        # Calculate item age distribution
        now = timezone.now()
        new_items = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include,
            created_at__gte=now - timezone.timedelta(days=30)
        ).count()
        
        medium_items = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include,
            created_at__lt=now - timezone.timedelta(days=30),
            created_at__gte=now - timezone.timedelta(days=90)
        ).count()
        
        old_items = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include,
            created_at__lt=now - timezone.timedelta(days=90)
        ).count()
        
        item_age_distribution = [
            {'name': 'New (< 30 days)', 'count': new_items, 'percentage': round((new_items / total_items) * 100, 1) if total_items > 0 else 0},
            {'name': 'Medium (30-90 days)', 'count': medium_items, 'percentage': round((medium_items / total_items) * 100, 1) if total_items > 0 else 0},
            {'name': 'Old (> 90 days)', 'count': old_items, 'percentage': round((old_items / total_items) * 100, 1) if total_items > 0 else 0},
        ]
        
        # Get recent activity - both additions and dispositions
        recent_additions = StockAddition.objects.filter(
            item__bin__shelf__rack__warehouse__in=warehouses_to_include
        ).order_by('-timestamp')[:5]
        
        recent_dispositions = Disposition.objects.filter(
            item__bin__shelf__rack__warehouse__in=warehouses_to_include
        ).order_by('-timestamp')[:5]
        
        # Combine and sort
        for addition in recent_additions:
            recent_activity.append({
                'item_name': addition.item.name,
                'type': 'Addition',
                'quantity': addition.quantity,
                'reason': addition.get_addition_type_display(),
                'timestamp': addition.timestamp,
                'user': addition.created_by.username,
                'item_url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': addition.item.bin.shelf.rack.warehouse.id,
                    'rack_id': addition.item.bin.shelf.rack.id,
                    'shelf_id': addition.item.bin.shelf.id,
                    'bin_id': addition.item.bin.id,
                    'item_id': addition.item.id
                })
            })
        
        for disposition in recent_dispositions:
            recent_activity.append({
                'item_name': disposition.item.name,
                'type': 'Disposition',
                'quantity': -disposition.quantity,  # Negative for removals
                'reason': disposition.get_disposition_type_display(),
                'timestamp': disposition.timestamp,
                'user': disposition.created_by.username,
                'item_url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': disposition.item.bin.shelf.rack.warehouse.id,
                    'rack_id': disposition.item.bin.shelf.rack.id,
                    'shelf_id': disposition.item.bin.shelf.id,
                    'bin_id': disposition.item.bin.id,
                    'item_id': disposition.item.id
                })
            })
        
        # Sort by timestamp
        recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:10]
            
    elif report_type == 'low_stock':
        report_title = "Low Stock Report"
        
        # Filter by warehouse if specified
        if warehouse_id and warehouse_id != 'all':
            warehouse_filter = Q(bin__shelf__rack__warehouse__id=warehouse_id)
        else:
            warehouse_filter = Q(bin__shelf__rack__warehouse__user=request.user)
        
        # Get low stock items using the threshold parameter
        low_stock_items_query = Item.objects.filter(
            warehouse_filter,
            quantity__lt=low_stock_threshold
        ).order_by('quantity')
        
        low_stock_count = low_stock_items_query.count()
        
        # Format low stock items for display with enhanced details
        for item in low_stock_items_query:
            bin_obj = item.bin
            shelf = bin_obj.shelf
            rack = shelf.rack
            warehouse = rack.warehouse
            
            # Calculate if stock is critically low (less than 20% of threshold)
            is_critical = item.quantity < (low_stock_threshold * 0.2)
            
            # Get recent dispositions to see rate of use
            recent_dispositions = Disposition.objects.filter(
                item=item
            ).order_by('-timestamp')[:5]
            
            disposition_rate = 0
            if recent_dispositions.exists():
                # Calculate average weekly usage if we have data
                oldest_disposition = recent_dispositions.last().timestamp
                newest_disposition = recent_dispositions.first().timestamp
                days_diff = (newest_disposition - oldest_disposition).days or 1  # Avoid divide by zero
                total_disposed = sum(d.quantity for d in recent_dispositions)
                disposition_rate = round((total_disposed / days_diff) * 7, 1)  # Weekly rate
            
            # Calculate estimated days until stockout
            days_until_stockout = float('inf') if disposition_rate == 0 else round(item.quantity / (disposition_rate / 7), 1)
            
            low_stock_items.append({
                'id': item.id,
                'name': item.name,
                'sku': item.sku or 'N/A',
                'quantity': item.quantity,
                'min_quantity': low_stock_threshold,
                'is_critical': is_critical,
                'warehouse': warehouse.name,
                'location': f"{warehouse.name} > {rack.name} > {shelf.name} > {bin_obj.name}",
                'weekly_usage': disposition_rate,
                'days_until_stockout': days_until_stockout if days_until_stockout != float('inf') else 'N/A',
                'last_updated': item.updated_at,
                'url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': warehouse.id,
                    'rack_id': rack.id,
                    'shelf_id': shelf.id,
                    'bin_id': bin_obj.id,
                    'item_id': item.id
                })
            })
            
        # Sort low stock items
        if sort_by == 'days_until_stockout':
            # Sort by days until stockout, putting "N/A" values at the end
            low_stock_items = sorted(
                low_stock_items, 
                key=lambda x: float('inf') if x['days_until_stockout'] == 'N/A' else x['days_until_stockout']
            )
        elif sort_by == 'weekly_usage':
            low_stock_items = sorted(low_stock_items, key=lambda x: x['weekly_usage'], reverse=True)
        else:  # Default to quantity
            low_stock_items = sorted(low_stock_items, key=lambda x: x['quantity'])
            
    elif report_type == 'warehouse_status':
        report_title = "Warehouse Status Report"
        
        # Filter warehouses
        if warehouse_id and warehouse_id != 'all':
            warehouses_to_include = warehouses.filter(id=warehouse_id)
        else:
            warehouses_to_include = warehouses
        
        # Apply time filter if specified
        time_condition = Q()
        if timeframe != 'all':
            time_threshold = timezone.now()
            if timeframe == 'day':
                time_threshold = time_threshold - timezone.timedelta(days=1)
            elif timeframe == 'week':
                time_threshold = time_threshold - timezone.timedelta(weeks=1)
            elif timeframe == 'month':
                time_threshold = time_threshold - timezone.timedelta(days=30)
            elif timeframe == 'quarter':
                time_threshold = time_threshold - timezone.timedelta(days=90)
            
            time_condition = Q(updated_at__gte=time_threshold)
        
        # Calculate capacity and other metrics for each warehouse
        total_capacity = 0
        
        for warehouse in warehouses_to_include:
            # Get racks, shelves, bins and items with time filter if applicable
            racks_query = Rack.objects.filter(warehouse=warehouse)
            if timeframe != 'all':
                racks_query = racks_query.filter(time_condition)
            racks_count = racks_query.count()
            
            shelves_query = Shelf.objects.filter(rack__warehouse=warehouse)
            if timeframe != 'all':
                shelves_query = shelves_query.filter(time_condition)
            shelves_count = shelves_query.count()
            
            bins_query = Bin.objects.filter(shelf__rack__warehouse=warehouse)
            if timeframe != 'all':
                bins_query = bins_query.filter(time_condition)
            bins_count = bins_query.count()
            
            items_query = Item.objects.filter(bin__shelf__rack__warehouse=warehouse)
            if timeframe != 'all':
                items_query = items_query.filter(time_condition)
            items_count = items_query.count()
            
            items_quantity = items_query.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Count bins with items for utilization calculation
            bins_with_items = Bin.objects.filter(
                shelf__rack__warehouse=warehouse,
                items__isnull=False
            ).distinct().count()
            
            bins_utilization = 0
            if bins_count > 0:
                bins_utilization = (bins_with_items / bins_count) * 100
            
            # Get item movement data
            additions_last_30_days = StockAddition.objects.filter(
                item__bin__shelf__rack__warehouse=warehouse,
                timestamp__gte=timezone.now() - timezone.timedelta(days=30)
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            dispositions_last_30_days = Disposition.objects.filter(
                item__bin__shelf__rack__warehouse=warehouse,
                timestamp__gte=timezone.now() - timezone.timedelta(days=30)
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate net change
            net_change_30_days = additions_last_30_days - dispositions_last_30_days
            
            # Calculate turnover rate (ratio of dispositions to average inventory)
            turnover_rate = 0
            if items_quantity > 0:
                turnover_rate = (dispositions_last_30_days / items_quantity) * 100
            
            # Better capacity calculation
            # Measure capacity utilization by quantity vs estimated max bins capacity
            theoretical_capacity = bins_count * 50  # Each bin could hold ~50 items (this is arbitrary)
            capacity = theoretical_capacity if theoretical_capacity > 0 else items_quantity * 2
            total_capacity += capacity
            
            capacity_used = 50  # Default to 50% for demo
            if capacity > 0:
                capacity_used = int((items_quantity / capacity) * 100)
            
            # Determine color based on capacity
            if capacity_used < 50:
                color = "success"
            elif capacity_used < 80:
                color = "warning"
            else:
                color = "danger"
            
            # Calculate empty bins
            empty_bins = bins_count - bins_with_items
            empty_bin_percentage = 0
            if bins_count > 0:
                empty_bin_percentage = (empty_bins / bins_count) * 100
            
            warehouse_stats.append({
                'id': warehouse.id,
                'name': warehouse.name,
                'capacity_used': capacity_used,
                'color': color,
                'racks': racks_count,
                'shelves': shelves_count,
                'bins': bins_count,
                'items': items_count,
                'quantity': items_quantity,
                'bins_utilization': round(bins_utilization, 1),
                'empty_bins': empty_bins,
                'empty_bin_percentage': round(empty_bin_percentage, 1),
                'additions_last_30_days': additions_last_30_days,
                'dispositions_last_30_days': dispositions_last_30_days,
                'net_change_30_days': net_change_30_days,
                'turnover_rate': round(turnover_rate, 1),
                'last_updated': warehouse.updated_at
            })
        
        # Sort warehouse stats
        if sort_by == 'capacity':
            warehouse_stats = sorted(warehouse_stats, key=lambda x: x['capacity_used'], reverse=True)
        elif sort_by == 'utilization':
            warehouse_stats = sorted(warehouse_stats, key=lambda x: x['bins_utilization'], reverse=True)
        elif sort_by == 'turnover':
            warehouse_stats = sorted(warehouse_stats, key=lambda x: x['turnover_rate'], reverse=True)
        elif sort_by == 'quantity':
            warehouse_stats = sorted(warehouse_stats, key=lambda x: x['quantity'], reverse=True)
        else:  # default to name
            warehouse_stats = sorted(warehouse_stats, key=lambda x: x['name'])
        
        # Calculate percentages for the progress bar
        for warehouse_stat in warehouse_stats:
            warehouse_capacity.append({
                'name': warehouse_stat['name'],
                'percentage': int((warehouse_stat['quantity'] / total_capacity) * 100) if total_capacity > 0 else 0,
                'color': warehouse_stat['color']
            })
            
        # Get item movement data
        for i in range(6):  # Last 6 months
            month_start = timezone.now() - timezone.timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timezone.timedelta(days=30 * i)
            
            # Ensure we're looking at complete months
            month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:  # Current month
                month_end = timezone.now()
            else:
                month_end = month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            month_name = month_start.strftime("%b %Y")
            
            additions = StockAddition.objects.filter(
                item__bin__shelf__rack__warehouse__in=warehouses_to_include,
                timestamp__gte=month_start,
                timestamp__lt=month_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            dispositions = Disposition.objects.filter(
                item__bin__shelf__rack__warehouse__in=warehouses_to_include,
                timestamp__gte=month_start,
                timestamp__lt=month_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            net_change = additions - dispositions
            
            movement_data.append({
                'month': month_name,
                'additions': additions,
                'dispositions': dispositions,
                'net_change': net_change
            })
        
        # Reverse to show chronological order
        movement_data.reverse()
            
    elif report_type == 'item_distribution':
        report_title = "Item Distribution Report"
        
        # Filter warehouses
        if warehouse_id and warehouse_id != 'all':
            warehouses_to_include = warehouses.filter(id=warehouse_id)
        else:
            warehouses_to_include = warehouses
        
        # Apply time filter if specified
        time_condition = Q()
        if timeframe != 'all':
            time_threshold = timezone.now()
            if timeframe == 'day':
                time_threshold = time_threshold - timezone.timedelta(days=1)
            elif timeframe == 'week':
                time_threshold = time_threshold - timezone.timedelta(weeks=1)
            elif timeframe == 'month':
                time_threshold = time_threshold - timezone.timedelta(days=30)
            elif timeframe == 'quarter':
                time_threshold = time_threshold - timezone.timedelta(days=90)
            
            time_condition = Q(updated_at__gte=time_threshold)
        
        # Get total items and quantity with filters
        items_query = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include
        )
        
        if timeframe != 'all':
            items_query = items_query.filter(time_condition)
        
        total_items = items_query.count()
        total_quantity = items_query.aggregate(total=Sum('quantity'))['total'] or 0
        
        # For this example, we'll create pseudo-categories based on the first letter of the item name
        # This is a stand-in for real categories which would require model changes
        category_counts = {}
        
        for item in items_query:
            # Create a pseudo-category based on first letter
            if item.name:
                first_letter = item.name[0].upper()
                category = f"Group {first_letter}"
                
                if category not in category_counts:
                    category_counts[category] = {
                        'items': 0,
                        'quantity': 0
                    }
                
                category_counts[category]['items'] += 1
                category_counts[category]['quantity'] += item.quantity
        
        # Convert to list format for template
        for category, counts in category_counts.items():
            if total_items > 0:
                percentage = round((counts['items'] / total_items) * 100, 1)
            else:
                percentage = 0
                
            category_distribution.append({
                'name': category,
                'items': counts['items'],
                'percentage': percentage,
                'quantity': counts['quantity']
            })
        
        # Sort category distribution
        if sort_by == 'items':
            category_distribution = sorted(category_distribution, key=lambda x: x['items'], reverse=True)
        elif sort_by == 'quantity':
            category_distribution = sorted(category_distribution, key=lambda x: x['quantity'], reverse=True)
        elif sort_by == 'percentage':
            category_distribution = sorted(category_distribution, key=lambda x: x['percentage'], reverse=True)
        else:  # default to name
            category_distribution = sorted(category_distribution, key=lambda x: x['name'])
        
        # Warehouse distribution with enhanced metrics
        for warehouse in warehouses_to_include:
            warehouse_items_query = Item.objects.filter(bin__shelf__rack__warehouse=warehouse)
            
            if timeframe != 'all':
                warehouse_items_query = warehouse_items_query.filter(time_condition)
            
            items_count = warehouse_items_query.count()
            items_quantity = warehouse_items_query.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate number of unique item names (products) in this warehouse
            unique_items = warehouse_items_query.values('name').distinct().count()
            
            # Calculate average quantity per item
            avg_quantity = 0
            if items_count > 0:
                avg_quantity = items_quantity / items_count
            
            if total_items > 0:
                percentage = round((items_count / total_items) * 100, 1)
            else:
                percentage = 0
                
            warehouse_distribution.append({
                'id': warehouse.id,
                'name': warehouse.name,
                'items': items_count,
                'unique_items': unique_items,
                'percentage': percentage,
                'quantity': items_quantity,
                'avg_quantity': round(avg_quantity, 1)
            })
        
        # Sort warehouse distribution
        if sort_by == 'items':
            warehouse_distribution = sorted(warehouse_distribution, key=lambda x: x['items'], reverse=True)
        elif sort_by == 'quantity':
            warehouse_distribution = sorted(warehouse_distribution, key=lambda x: x['quantity'], reverse=True)
        elif sort_by == 'unique_items':
            warehouse_distribution = sorted(warehouse_distribution, key=lambda x: x['unique_items'], reverse=True)
        else:  # default to name
            warehouse_distribution = sorted(warehouse_distribution, key=lambda x: x['name'])
        
        # Item age distribution calculation
        now = timezone.now()
        
        new_items = items_query.filter(created_at__gte=now - timezone.timedelta(days=30)).count()
        medium_items = items_query.filter(
            created_at__lt=now - timezone.timedelta(days=30),
            created_at__gte=now - timezone.timedelta(days=90)
        ).count()
        old_items = items_query.filter(created_at__lt=now - timezone.timedelta(days=90)).count()
        
        if total_items > 0:
            new_percentage = round((new_items / total_items) * 100, 1)
            medium_percentage = round((medium_items / total_items) * 100, 1)
            old_percentage = round((old_items / total_items) * 100, 1)
        else:
            new_percentage = medium_percentage = old_percentage = 0
        
        item_age_distribution = [
            {'name': 'New (< 30 days)', 'count': new_items, 'percentage': new_percentage},
            {'name': 'Medium (30-90 days)', 'count': medium_items, 'percentage': medium_percentage},
            {'name': 'Old (> 90 days)', 'count': old_items, 'percentage': old_percentage},
        ]
    
    context = {
        'report_type': report_type,
        'warehouse_id': warehouse_id if warehouse_id else 'all',
        'warehouses': warehouses,
        'report_title': report_title,
        'generation_time': generation_time,
        'timeframe': timeframe,
        'low_stock_threshold': low_stock_threshold,
        'sort_by': sort_by,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'total_bins': total_bins,
        'warehouse_data': warehouse_data,
        'top_items': top_items,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'warehouse_capacity': warehouse_capacity,
        'warehouse_stats': warehouse_stats,
        'category_distribution': category_distribution,
        'warehouse_distribution': warehouse_distribution,
        'item_age_distribution': item_age_distribution,
        'inventory_value': inventory_value,
        'recent_activity': recent_activity,
        'movement_data': movement_data,
    }
    
    return render(request, 'inventory/report.html', context)

def export_low_stock(request):
    """
    Export low stock items to CSV with enhanced information.
    """
    # Get parameters from request
    warehouse_id = request.GET.get('warehouse')
    low_stock_threshold = request.GET.get('threshold', 5)
    sort_by = request.GET.get('sort_by', 'quantity')
    
    try:
        low_stock_threshold = int(low_stock_threshold)
    except (ValueError, TypeError):
        low_stock_threshold = 5
    
    # Filter by warehouse if specified
    if warehouse_id and warehouse_id != 'all':
        warehouse_filter = Q(bin__shelf__rack__warehouse__id=warehouse_id)
    else:
        warehouse_filter = Q(bin__shelf__rack__warehouse__user=request.user)
    
    # Get low stock items
    low_stock_items = Item.objects.filter(
        warehouse_filter,
        quantity__lt=low_stock_threshold
    )
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="low_stock_items_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create the CSV writer
    writer = csv.writer(response)
    
    # Write the header row with enhanced columns
    writer.writerow([
        'Item Name', 
        'SKU', 
        'Current Quantity', 
        'Min Threshold', 
        'Weekly Usage', 
        'Days Until Empty', 
        'Last Updated', 
        'Warehouse', 
        'Rack', 
        'Shelf', 
        'Bin',
        'Critically Low'
    ])
    
    # Process and write the data rows
    for item in low_stock_items:
        # Calculate if stock is critically low (less than 20% of threshold)
        is_critical = item.quantity < (low_stock_threshold * 0.2)
        
        # Get recent dispositions to see rate of use
        recent_dispositions = Disposition.objects.filter(
            item=item
        ).order_by('-timestamp')[:5]
        
        disposition_rate = 0
        if recent_dispositions.exists():
            # Calculate average weekly usage if we have data
            oldest_disposition = recent_dispositions.last().timestamp
            newest_disposition = recent_dispositions.first().timestamp
            days_diff = (newest_disposition - oldest_disposition).days or 1  # Avoid divide by zero
            total_disposed = sum(d.quantity for d in recent_dispositions)
            disposition_rate = round((total_disposed / days_diff) * 7, 1)  # Weekly rate
        
        # Calculate estimated days until stockout
        days_until_stockout = "N/A" if disposition_rate == 0 else round(item.quantity / (disposition_rate / 7), 1)
        
        writer.writerow([
            item.name,
            item.sku or 'N/A',
            item.quantity,
            low_stock_threshold,
            disposition_rate,
            days_until_stockout,
            item.updated_at.strftime("%Y-%m-%d"),
            item.bin.shelf.rack.warehouse.name,
            item.bin.shelf.rack.name,
            item.bin.shelf.name,
            item.bin.name,
            "Yes" if is_critical else "No"
        ])
    
    return response
# Error handler view
def handle_error(request, error_title=None, error_message=None, error_details=None, back_url=None):
    """
    Generic error handler view.
    """
    context = {
        'error_title': error_title or "Error",
        'error_message': error_message or "An unexpected error occurred.",
        'error_details': error_details,
        'back_url': back_url
    }
    
    return render(request, 'inventory/error.html', context)

def item_disposition(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Record a disposition for an item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    if request.method == 'POST':
        form = DispositionForm(request.POST, item=item)
        if form.is_valid():
            disposition = form.save(commit=False)
            disposition.item = item
            disposition.created_by = request.user
            disposition.save()
            
            # Update item quantity
            item.quantity -= disposition.quantity
            item.save()
            
            messages.success(
                request, 
                f'Successfully recorded disposition of {disposition.quantity} units of "{item.name}".'
            )
            
            # If the item quantity is now 0, suggest deletion
            if item.quantity == 0:
                messages.info(
                    request,
                    f'Item "{item.name}" now has 0 quantity. You may want to delete it.'
                )
            
            return redirect('inventory:item-detail', 
                           warehouse_id=warehouse.id, 
                           rack_id=rack.id,
                           shelf_id=shelf.id,
                           bin_id=bin_obj.id,
                           item_id=item.id)
    else:
        form = DispositionForm(item=item)
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item
    }
    
    return render(request, 'inventory/item_disposition.html', context)

def item_add_stock(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Record a stock addition for an item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    if request.method == 'POST':
        form = StockAdditionForm(request.POST)
        if form.is_valid():
            addition = form.save(commit=False)
            addition.item = item
            addition.created_by = request.user
            addition.save()
            
            # Update item quantity
            item.quantity += addition.quantity
            item.save()
            
            messages.success(
                request, 
                f'Successfully added {addition.quantity} units of "{item.name}".'
            )
            
            # Determine where to redirect based on referer
            referer = request.META.get('HTTP_REFERER', '')
            if 'bin-detail' in referer:
                return redirect('inventory:bin-detail', 
                               warehouse_id=warehouse.id, 
                               rack_id=rack.id,
                               shelf_id=shelf.id,
                               bin_id=bin_obj.id)
            else:
                return redirect('inventory:item-detail', 
                               warehouse_id=warehouse.id, 
                               rack_id=rack.id,
                               shelf_id=shelf.id,
                               bin_id=bin_obj.id,
                               item_id=item.id)
    else:
        form = StockAdditionForm(initial={'quantity': 1})
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item
    }
    
    return render(request, 'inventory/item_add_stock.html', context)