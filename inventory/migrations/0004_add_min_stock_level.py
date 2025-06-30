# Create a new migration file: inventory/migrations/0004_add_min_stock_level.py
# Run: python manage.py makemigrations inventory --name add_min_stock_level
# Then: python manage.py migrate

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_stockaddition'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='min_stock_level',
            field=models.PositiveIntegerField(default=0, help_text='Minimum stock level before item is considered low stock'),
        ),
    ]