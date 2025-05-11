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

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity}) in {self.bin}"

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