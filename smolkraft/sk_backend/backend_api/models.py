from django.db import models
from django.conf import settings


UNITS_OF_MEASURE = {
    'C': 'Cup',
    'CL': 'Centiliter',
    'CM': 'Centimeter',
    'DL': 'Deciliter',
    'FLOZ': 'Fluid Ounce (volume)',
    'G': 'Gram',
    'IN': 'Inch',
    'KG': 'Kilogram',
    'L': 'Liter',
    'LB': 'Pound',
    'M': 'Meter',
    'MG': 'Milligram',
    'ML': 'Milliliter',
    'MM': 'Millimeter',
    'OZ': 'Dry Ounce (weight)',
    'PC': 'Piece',
    'TBSP': 'Tablespoon',
    'THOU': 'Thousandth-inch',
    'TSP': 'Teaspoon',
    'UNIT': 'Unit',
    'YD': 'Yard',
}


class UnitConversion(models.Model):
    from_unit_name = models.CharField(max_length=32)
    to_unit_name = models.CharField(max_length=32)
    multiply_by = models.DecimalField(max_digits=16, decimal_places=10)


class BaseTable(models.Model):
    # related_name='+' disables reverse relations to avoid accessor clashes
    insert_user = models.IntegerField(db_index=True)
    insert_dttm = models.DateTimeField(auto_now_add=True)
    update_user = models.IntegerField(db_index=True)
    update_dttm = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Vendor(BaseTable):
    vendor_name = models.CharField(max_length=256)

    def __str__(self):
        return self.vendor_name


class OrderHeader(BaseTable):
    owner_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.CASCADE)
    cost_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    cost_tax = models.DecimalField(max_digits=10, decimal_places=2)
    cost_shipping = models.DecimalField(max_digits=10, decimal_places=2)
    cost_discount = models.DecimalField(max_digits=10, decimal_places=2)
    cost_total = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField()
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    vendor_order_id = models.CharField(max_length=128)
    order_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['owner_user_id', 'vendor', 'cost_total'],
                name='unique_order_header_per_user_vendor_cost'
            )
        ]


class Material(BaseTable):
    """Replaces RawMaterial - can be raw materials, manufactured items, etc."""
    description = models.CharField(max_length=512)
    short_name = models.CharField(max_length=64)
    # Self-reference for materials that are manufactured internally
    bom_header = models.ForeignKey('BOMHeader', on_delete=models.CASCADE, null=True, blank=True,
                                   help_text="Link to the Bill of Materials if this item is manufactured internally.")


class OrderLineItem(BaseTable):
    owner_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_header = models.ForeignKey(OrderHeader, on_delete=models.PROTECT)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)  # Changed from raw_material
    item_count = models.IntegerField()
    sku = models.CharField(max_length=128, blank=True)
    upc = models.CharField(max_length=128, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_amount = models.DecimalField(max_digits=12, decimal_places=4)
    unit_uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)


class BOMHeader(BaseTable):
    """Replaces RecipeHeader - standard Bill of Materials header"""
    owner_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=64)  # Changed from recipe_name
    description = models.CharField(max_length=256)  # Changed from recipe_description
    output_quantity = models.DecimalField(max_digits=12, decimal_places=4)  # Changed from yield_amount
    output_uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)  # Changed from yield_uom

    def __str__(self):
        return self.product_name


class BOMLine(BaseTable):
    """Replaces RecipeAmount - Bill of Materials line items"""
    bom_header = models.ForeignKey(BOMHeader, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)  # Changed from raw_material
    quantity = models.DecimalField(max_digits=14, decimal_places=6)  # Changed from recipe_amount
    uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)  # Changed from recipe_amount_uom


class BOOHeader(BaseTable):
    """Replaces InstructionSet - Bill of Operations header"""
    bom_header = models.OneToOneField(BOMHeader, on_delete=models.CASCADE)

    def __str__(self):
        return f"Operations for {self.bom_header.product_name}"


class Operation(BaseTable):
    """Replaces Instruction - individual operations in the manufacturing process"""
    boo_header = models.ForeignKey(BOOHeader, on_delete=models.CASCADE)  # Changed from instruction_set
    description = models.CharField(max_length=3000)  # Changed from instruction_text
    sequence_number = models.PositiveSmallIntegerField()  # Changed from instruction_sequence_number
    estimated_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added field
    time_uom = models.CharField(max_length=10, null=True, blank=True)  # Added field (minutes, hours, etc.)

    class Meta:
        ordering = ['sequence_number']


class ProductionOrder(BaseTable):
    """Replaces Batch - represents a production run"""
    owner_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bom_header = models.ForeignKey(BOMHeader, on_delete=models.RESTRICT)  # Changed from recipe_header
    production_date = models.DateField()  # Changed from batch_date
    quantity = models.PositiveSmallIntegerField()  # Changed from yield_count
    status = models.CharField(max_length=20, default='planned',  # Added status field
                              choices=[
                                  ('planned', 'Planned'),
                                  ('in_progress', 'In Progress'),
                                  ('completed', 'Completed'),
                                  ('cancelled', 'Cancelled')
                              ])

    def __str__(self):
        return f"PO-{self.id}: {self.bom_header.product_name} ({self.quantity})"


class Inventory(BaseTable):
    """Replaces CurrentStock - tracks inventory levels"""
    owner_user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)  # Changed approach
    quantity = models.DecimalField(max_digits=14, decimal_places=6)  # Added quantity field
    uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)  # Added UOM
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.RESTRICT, null=True, blank=True)  # Optional link to production
    location = models.CharField(max_length=50, blank=True)  # Added location