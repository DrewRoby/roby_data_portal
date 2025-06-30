# inventory/utils.py
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from datetime import timedelta
from .models import StockAddition, Disposition


def get_activity_data(user, hours_limit=24, warehouse_id=None, activity_type=None, limit=None):
    """
    Get combined activity data from StockAddition and Disposition models.
    
    Args:
        user: The user to filter activities for
        hours_limit: Number of hours to look back (None for no limit)
        warehouse_id: Specific warehouse ID to filter by (None for all warehouses)
        activity_type: 'addition', 'disposition', or None for both
        limit: Maximum number of activities to return (None for no limit)
    
    Returns:
        List of activity dictionaries sorted by timestamp (newest first)
    """
    # Calculate time threshold
    time_threshold = None
    if hours_limit:
        time_threshold = timezone.now() - timedelta(hours=hours_limit)
    
    # Base filter for user's warehouses
    base_filter = Q(item__bin__shelf__rack__warehouse__user=user)
    
    # Add warehouse filter if specified
    if warehouse_id:
        base_filter &= Q(item__bin__shelf__rack__warehouse__id=warehouse_id)
    
    # Add time filter if specified
    if time_threshold:
        time_filter = Q(timestamp__gte=time_threshold)
    else:
        time_filter = Q()
    
    activities = []
    
    # Get StockAdditions if requested
    if activity_type in [None, 'addition']:
        additions = StockAddition.objects.filter(
            base_filter & time_filter
        ).select_related(
            'item__bin__shelf__rack__warehouse',
            'created_by'
        ).order_by('-timestamp')
        
        for addition in additions:
            activities.append({
                'id': f"addition_{addition.id}",
                'item_name': addition.item.name,
                'item_sku': addition.item.sku or 'N/A',
                'type': 'addition',
                'type_display': 'Stock Addition',
                'quantity': addition.quantity,
                'quantity_display': f"+{addition.quantity}",
                'reason': addition.get_addition_type_display(),
                'notes': addition.notes,
                'timestamp': addition.timestamp,
                'user': addition.created_by.username,
                'warehouse_name': addition.item.bin.shelf.rack.warehouse.name,
                'location': f"{addition.item.bin.shelf.rack.warehouse.name} > {addition.item.bin.shelf.rack.name} > {addition.item.bin.shelf.name} > {addition.item.bin.name}",
                'item_url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': addition.item.bin.shelf.rack.warehouse.id,
                    'rack_id': addition.item.bin.shelf.rack.id,
                    'shelf_id': addition.item.bin.shelf.id,
                    'bin_id': addition.item.bin.id,
                    'item_id': addition.item.id
                }),
                'badge_class': 'bg-success'
            })
    
    # Get Dispositions if requested
    if activity_type in [None, 'disposition']:
        dispositions = Disposition.objects.filter(
            base_filter & time_filter
        ).select_related(
            'item__bin__shelf__rack__warehouse',
            'created_by'
        ).order_by('-timestamp')
        
        for disposition in dispositions:
            activities.append({
                'id': f"disposition_{disposition.id}",
                'item_name': disposition.item.name,
                'item_sku': disposition.item.sku or 'N/A',
                'type': 'disposition',
                'type_display': 'Stock Disposition',
                'quantity': disposition.quantity,
                'quantity_display': f"-{disposition.quantity}",
                'reason': disposition.get_disposition_type_display(),
                'notes': disposition.notes,
                'timestamp': disposition.timestamp,
                'user': disposition.created_by.username,
                'warehouse_name': disposition.item.bin.shelf.rack.warehouse.name,
                'location': f"{disposition.item.bin.shelf.rack.warehouse.name} > {disposition.item.bin.shelf.rack.name} > {disposition.item.bin.shelf.name} > {disposition.item.bin.name}",
                'item_url': reverse('inventory:item-detail', kwargs={
                    'warehouse_id': disposition.item.bin.shelf.rack.warehouse.id,
                    'rack_id': disposition.item.bin.shelf.rack.id,
                    'shelf_id': disposition.item.bin.shelf.id,
                    'bin_id': disposition.item.bin.id,
                    'item_id': disposition.item.id
                }),
                'badge_class': 'bg-danger'
            })
    
    # Sort by timestamp (newest first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply limit if specified
    if limit:
        activities = activities[:limit]
    
    return activities


def get_activity_summary(user, hours_limit=24):
    """
    Get a summary of activity for dashboard display.
    
    Args:
        user: The user to get summary for
        hours_limit: Number of hours to look back
    
    Returns:
        Dictionary with activity counts and recent activities
    """
    activities = get_activity_data(user, hours_limit=hours_limit, limit=10)
    
    # Count by type
    addition_count = len([a for a in activities if a['type'] == 'addition'])
    disposition_count = len([a for a in activities if a['type'] == 'disposition'])
    
    return {
        'recent_activities': activities,
        'total_count': len(activities),
        'addition_count': addition_count,
        'disposition_count': disposition_count,
    }


def generate_csv_export(data, field_mappings, filename_prefix):
    """
    Generate CSV export from data with flexible field mapping.
    
    Args:
        data: List of dictionaries containing the data to export
        field_mappings: List of tuples (field_key, csv_header, transform_func)
        filename_prefix: Prefix for the filename (e.g., 'inventory_activity')
    
    Returns:
        HttpResponse with CSV content and appropriate headers
    """
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    # Generate filename with timestamp
    timestamp = timezone.now().strftime('%Y-%m-%d')
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    headers = [mapping[1] for mapping in field_mappings]
    writer.writerow(headers)
    
    # Write data rows
    for item in data:
        row = []
        for field_key, header, transform_func in field_mappings:
            value = item.get(field_key, '')
            
            # Apply transformation function if provided
            if transform_func and value:
                try:
                    value = transform_func(value)
                except:
                    value = str(value)  # Fallback to string conversion
            
            row.append(value)
        
        writer.writerow(row)
    
    return response


def export_activity_csv(user, hours_limit=None, warehouse_id=None, activity_type=None):
    """
    Export activity data to CSV with proper formatting.
    
    Args:
        user: The user to get activities for
        hours_limit: Number of hours to look back (None for all time)
        warehouse_id: Specific warehouse ID to filter by (None for all)
        activity_type: 'addition', 'disposition', or None for both
    
    Returns:
        HttpResponse with CSV content
    """
    # Get the activity data
    activities = get_activity_data(
        user=user,
        hours_limit=hours_limit,
        warehouse_id=warehouse_id,
        activity_type=activity_type
    )
    
    # Define field mappings for activity CSV
    field_mappings = [
        ('item_name', 'Item Name', None),
        ('item_sku', 'SKU', None),
        ('type_display', 'Activity Type', None),
        ('quantity_display', 'Quantity Change', None),
        ('reason', 'Reason', None),
        ('notes', 'Notes', None),
        ('warehouse_name', 'Warehouse', None),
        ('user', 'User', None),
        ('timestamp', 'Date/Time', lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S')),
    ]
    
    return generate_csv_export(activities, field_mappings, 'inventory_activity')


def export_report_csv(data, report_type):
    """
    Export report data to CSV with appropriate formatting.
    
    Args:
        data: The report data (list of dictionaries)
        report_type: Type of report for filename generation
    
    Returns:
        HttpResponse with CSV content
    """
    if report_type == 'low_stock':
        field_mappings = [
            ('name', 'Item Name', None),
            ('sku', 'SKU', None),
            ('quantity', 'Current Quantity', None),
            ('days_in_stock', 'Days in Stock', None),
            ('warehouse', 'Warehouse', None),
            ('location', 'Full Location', None),
        ]
        filename_prefix = 'inventory_report_low_stock'
        
    elif report_type == 'inventory_summary':
        field_mappings = [
            ('name', 'Item Name', None),
            ('sku', 'SKU', None),
            ('quantity', 'Quantity', None),
            ('warehouse', 'Warehouse', None),
            ('location', 'Location', None),
            ('days_in_stock', 'Days in Stock', None),
        ]
        filename_prefix = 'inventory_report_summary'
        
    elif report_type == 'recent_activity':
        # For activity within reports
        field_mappings = [
            ('item_name', 'Item Name', None),
            ('type', 'Activity Type', None),
            ('quantity', 'Quantity', None),
            ('reason', 'Reason', None),
            ('user', 'User', None),
            ('timestamp', 'Date/Time', lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S')),
        ]
        filename_prefix = 'inventory_report_recent_activity'
        
    else:
        # Generic fallback
        if data and len(data) > 0:
            # Auto-generate mappings from first item keys
            field_mappings = [(key, key.replace('_', ' ').title(), None) for key in data[0].keys()]
        else:
            field_mappings = []
        filename_prefix = f'inventory_report_{report_type}'
    
    return generate_csv_export(data, field_mappings, filename_prefix)