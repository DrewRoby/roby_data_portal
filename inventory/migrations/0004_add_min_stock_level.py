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