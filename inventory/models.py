from django.db import models
from django.contrib.auth.models import User

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warehouses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Rack(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='racks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"

class Shelf(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='shelves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rack.warehouse.name} - {self.rack.name} - {self.name}"

class Bin(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name='bins')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shelf.rack.warehouse.name} - {self.shelf.rack.name} - {self.shelf.name} - {self.name}"

# Add this field to the Item model in inventory/models.py

class Item(models.Model):
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(
        default=0, 
        help_text='Minimum stock level before item is considered low stock'
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['bin', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.bin})"
    
    @property 
    def is_low_stock(self):
        """Return True if current quantity is below minimum stock level."""
        return self.quantity < self.min_stock_level
    
    @property
    def stock_status(self):
        """Return descriptive stock status."""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"

class Disposition(models.Model):
    DISPOSITION_TYPES = [
        ('sold', 'Sold'),
        ('waste', 'Waste/Expired'),
        ('damaged', 'Damaged'),
        ('transferred', 'Transferred Externally'),
        ('returned', 'Returned to Supplier'),
        ('other', 'Other')
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='dispositions')
    quantity = models.PositiveIntegerField()
    disposition_type = models.CharField(max_length=20, choices=DISPOSITION_TYPES)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.get_disposition_type_display()} - {self.quantity} units of {self.item.name}"

class StockAddition(models.Model):
    ADDITION_TYPES = [
        ('new_stock', 'New Stock'),
        ('manufactured', 'Manufactured'),
        ('returned', 'Returned Stock'),
        ('correction', 'Inventory Correction'),
        ('other', 'Other')
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='additions')
    quantity = models.PositiveIntegerField()
    addition_type = models.CharField(max_length=20, choices=ADDITION_TYPES)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.get_addition_type_display()} - {self.quantity} units of {self.item.name}"