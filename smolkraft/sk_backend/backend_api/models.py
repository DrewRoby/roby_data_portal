# backend_api/models.py
from django.db import models


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
    # Was: ForeignKey(settings.AUTH_USER_MODEL) — DB column was owner_user_id_id.
    # Now: plain IntegerField storing request.user.id from the portal DB.
    owner_user_id = models.IntegerField(db_index=True)
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
    description = models.CharField(max_length=512)
    short_name = models.CharField(max_length=64)
    bom_header = models.ForeignKey(
        'BOMHeader',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Link to the Bill of Materials if this item is manufactured internally.",
    )


class OrderLineItem(BaseTable):
    # Was: ForeignKey(settings.AUTH_USER_MODEL)
    owner_user_id = models.IntegerField(db_index=True)
    order_header = models.ForeignKey(OrderHeader, on_delete=models.PROTECT)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    item_count = models.IntegerField()
    sku = models.CharField(max_length=128, blank=True)
    upc = models.CharField(max_length=128, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_amount = models.DecimalField(max_digits=12, decimal_places=4)
    unit_uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)


class BOMHeader(BaseTable):
    # Was: ForeignKey(settings.AUTH_USER_MODEL)
    owner_user_id = models.IntegerField(db_index=True)
    product_name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    output_quantity = models.DecimalField(max_digits=12, decimal_places=4)
    output_uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)

    def __str__(self):
        return self.product_name


class BOMLine(BaseTable):
    bom_header = models.ForeignKey(BOMHeader, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=6)
    uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)


class BOOHeader(BaseTable):
    bom_header = models.OneToOneField(BOMHeader, on_delete=models.CASCADE)

    def __str__(self):
        return f"Operations for {self.bom_header.product_name}"


class Operation(BaseTable):
    boo_header = models.ForeignKey(BOOHeader, on_delete=models.CASCADE)
    description = models.CharField(max_length=3000)
    sequence_number = models.PositiveSmallIntegerField()
    estimated_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time_uom = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        ordering = ['sequence_number']


class ProductionOrder(BaseTable):
    # Was: ForeignKey(settings.AUTH_USER_MODEL)
    owner_user_id = models.IntegerField(db_index=True)
    bom_header = models.ForeignKey(BOMHeader, on_delete=models.RESTRICT)
    production_date = models.DateField()
    quantity = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20,
        default='planned',
        choices=[
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
    )

    def __str__(self):
        return f"PO-{self.id}: {self.bom_header.product_name} ({self.quantity})"


class Inventory(BaseTable):
    # Was: ForeignKey(settings.AUTH_USER_MODEL)
    owner_user_id = models.IntegerField(db_index=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=6)
    uom = models.CharField(max_length=4, choices=UNITS_OF_MEASURE)
    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=50, blank=True)