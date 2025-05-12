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

from .models import Warehouse, Rack, Shelf, Bin, Item
from .forms import (
    WarehouseForm, RackForm, ShelfForm, BinForm, ItemForm,
    ItemTransferForm, RestockForm, SearchForm, DispositionForm
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
def item_detail(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Display details of a specific item.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    dispositions = item.dispositions.all().order_by('-timestamp')
    
    context = {
        'warehouse': warehouse,
        'rack': rack,
        'shelf': shelf,
        'bin': bin_obj,
        'item': item,
        'dispositions': dispositions
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

def item_quantity_update(request, warehouse_id, rack_id, shelf_id, bin_id, item_id):
    """
    Quick update of item quantity from the detail page.
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, user=request.user)
    rack = get_object_or_404(Rack, id=rack_id, warehouse=warehouse)
    shelf = get_object_or_404(Shelf, id=shelf_id, rack=rack)
    bin_obj = get_object_or_404(Bin, id=bin_id, shelf=shelf)
    item = get_object_or_404(Item, id=item_id, bin=bin_obj)
    
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 0))
            if new_quantity >= 0:
                old_quantity = item.quantity
                item.quantity = new_quantity
                item.save()
                
                if new_quantity > old_quantity:
                    messages.success(request, f'Quantity of "{item.name}" increased from {old_quantity} to {new_quantity}.')
                elif new_quantity < old_quantity:
                    messages.warning(request, f'Quantity of "{item.name}" decreased from {old_quantity} to {new_quantity}.')
                else:
                    messages.info(request, f'Quantity of "{item.name}" remains unchanged at {new_quantity}.')
            else:
                messages.error(request, 'Quantity cannot be negative.')
        except ValueError:
            messages.error(request, 'Invalid quantity value.')
    
    return redirect('inventory:item-detail', 
                   warehouse_id=warehouse.id, 
                   rack_id=rack.id,
                   shelf_id=shelf.id,
                   bin_id=bin_obj.id,
                   item_id=item.id)

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

def report(request):
    """
    Generate inventory reports.
    """
    report_type = request.GET.get('report_type')
    warehouse_id = request.GET.get('warehouse')
    
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
        
        # Get warehouse-specific data
        for warehouse in warehouses_to_include:
            racks_count = Rack.objects.filter(warehouse=warehouse).count()
            shelves_count = Shelf.objects.filter(rack__warehouse=warehouse).count()
            bins_count = Bin.objects.filter(shelf__rack__warehouse=warehouse).count()
            items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
            items_quantity = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).aggregate(
                total=Sum('quantity'))['total'] or 0
            
            warehouse_data.append({
                'name': warehouse.name,
                'items': items_count,
                'quantity': items_quantity,
                'racks': racks_count,
                'shelves': shelves_count,
                'bins': bins_count
            })
        
        # Get top stocked items
        top_items = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include
        ).order_by('-quantity')[:10]
        
        # Format top items for display
        formatted_top_items = []
        for item in top_items:
            formatted_top_items.append({
                'name': item.name,
                'sku': item.sku,
                'quantity': item.quantity,
                'location': f"{item.bin.shelf.rack.warehouse.name} > {item.bin.shelf.rack.name} > {item.bin.shelf.name} > {item.bin.name}"
            })
        top_items = formatted_top_items
        
    elif report_type == 'low_stock':
        report_title = "Low Stock Report"
        
        # Filter by warehouse if specified
        if warehouse_id and warehouse_id != 'all':
            warehouse_filter = Q(bin__shelf__rack__warehouse__id=warehouse_id)
        else:
            warehouse_filter = Q(bin__shelf__rack__warehouse__user=request.user)
        
        # Get low stock items
        low_stock_items_query = Item.objects.filter(
            warehouse_filter,
            quantity__lt=5  # Using 5 as the threshold for this example
        ).order_by('quantity')
        
        low_stock_count = low_stock_items_query.count()
        
        # Format low stock items for display
        for item in low_stock_items_query:
            low_stock_items.append({
                'name': item.name,
                'sku': item.sku,
                'quantity': item.quantity,
                'min_quantity': 5,  # This would be a field on the Item model in a real application
                'location': f"{item.bin.shelf.rack.warehouse.name} > {item.bin.shelf.rack.name} > {item.bin.shelf.name} > {item.bin.name}",
                'url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': item.bin.shelf.rack.warehouse.id,
                    'rack_id': item.bin.shelf.rack.id,
                    'shelf_id': item.bin.shelf.id,
                    'bin_id': item.bin.id,
                    'item_id': item.id
                })
            })
            
    elif report_type == 'warehouse_status':
        report_title = "Warehouse Status Report"
        
        # Filter warehouses
        if warehouse_id and warehouse_id != 'all':
            warehouses_to_include = warehouses.filter(id=warehouse_id)
        else:
            warehouses_to_include = warehouses
        
        # Calculate capacity for each warehouse
        total_capacity = 0
        
        for warehouse in warehouses_to_include:
            # In a real application, this would be calculated based on actual capacity metrics
            # For this example, we'll use an arbitrary calculation
            racks_count = Rack.objects.filter(warehouse=warehouse).count()
            bins_count = Bin.objects.filter(shelf__rack__warehouse=warehouse).count()
            items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
            items_quantity = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).aggregate(
                total=Sum('quantity'))['total'] or 0
            
            # Arbitrary capacity calculation for the example
            capacity = items_quantity * 2  # Assume each warehouse can hold twice its current quantity
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
            
            warehouse_stats.append({
                'id': warehouse.id,
                'name': warehouse.name,
                'capacity_used': capacity_used,
                'color': color,
                'racks': racks_count,
                'shelves': Shelf.objects.filter(rack__warehouse=warehouse).count(),
                'bins': bins_count,
                'items': items_count,
                'quantity': items_quantity
            })
        
        # Calculate percentages for the progress bar
        for warehouse_stat in warehouse_stats:
            warehouse_capacity.append({
                'name': warehouse_stat['name'],
                'percentage': int((warehouse_stat['quantity'] / total_capacity) * 100) if total_capacity > 0 else 0,
                'color': warehouse_stat['color']
            })
            
    elif report_type == 'item_distribution':
        report_title = "Item Distribution Report"
        
        # Filter warehouses
        if warehouse_id and warehouse_id != 'all':
            warehouses_to_include = warehouses.filter(id=warehouse_id)
        else:
            warehouses_to_include = warehouses
        
        # Get total items and quantity
        total_items = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include
        ).count()
        
        total_quantity = Item.objects.filter(
            bin__shelf__rack__warehouse__in=warehouses_to_include
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # For this example, we'll mock category distribution
        # In a real application, categories would be a field on the Item model
        mock_categories = ["Electronics", "Office Supplies", "Furniture", "Tools", "Raw Materials"]
        
        # Create mock distribution data
        import random
        random.seed(42)  # For consistent demo data
        
        remaining_items = total_items
        remaining_quantity = total_quantity
        
        for i, category in enumerate(mock_categories):
            if i == len(mock_categories) - 1:
                # Last category gets all remaining items
                cat_items = remaining_items
                cat_quantity = remaining_quantity
            else:
                # Distribute items randomly
                cat_items = random.randint(1, remaining_items // 2) if remaining_items > 1 else 0
                cat_quantity = random.randint(1, remaining_quantity // 2) if remaining_quantity > 1 else 0
                
                remaining_items -= cat_items
                remaining_quantity -= cat_quantity
            
            if total_items > 0 and cat_items > 0:
                percentage = int((cat_items / total_items) * 100)
            else:
                percentage = 0
                
            category_distribution.append({
                'name': category,
                'items': cat_items,
                'percentage': percentage,
                'quantity': cat_quantity
            })
        
        # Warehouse distribution
        for warehouse in warehouses_to_include:
            items_count = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).count()
            items_quantity = Item.objects.filter(bin__shelf__rack__warehouse=warehouse).aggregate(
                total=Sum('quantity'))['total'] or 0
            
            if total_items > 0:
                percentage = int((items_count / total_items) * 100)
            else:
                percentage = 0
                
            warehouse_distribution.append({
                'name': warehouse.name,
                'items': items_count,
                'percentage': percentage,
                'quantity': items_quantity
            })
    
    context = {
        'report_type': report_type,
        'warehouse_id': warehouse_id if warehouse_id else 'all',
        'warehouses': warehouses,
        'report_title': report_title,
        'generation_time': generation_time,
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
        'warehouse_distribution': warehouse_distribution
    }
    
    return render(request, 'inventory/report.html', context)

def export_low_stock(request):
    """
    Export low stock items to CSV.
    """
    # Get low stock items
    low_stock_items = Item.objects.filter(
        bin__shelf__rack__warehouse__user=request.user,
        quantity__lt=5  # Using 5 as the threshold for this example
    ).order_by('quantity')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="low_stock_items_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create the CSV writer
    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow(['Item Name', 'SKU', 'Current Quantity', 'Min Threshold', 'Warehouse', 'Rack', 'Shelf', 'Bin'])
    
    # Write the data rows
    for item in low_stock_items:
        writer.writerow([
            item.name,
            item.sku or 'N/A',
            item.quantity,
            5,  # This would be a field in a real application
            item.bin.shelf.rack.warehouse.name,
            item.bin.shelf.rack.name,
            item.bin.shelf.name,
            item.bin.name
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