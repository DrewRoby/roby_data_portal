from django.db import migrations

def create_events_app(apps, schema_editor):
    App = apps.get_model('portal', 'App')
    
    # Create Events app entry
    events_app, created = App.objects.get_or_create(
        app_id='events',
        defaults={
            'name': 'Events',
            'description': 'Plan and manage events with multiple spaces and agenda items',
            'icon': 'fa-calendar-alt',
            'background_color': '#673AB7',
            'link': '/events/',
            'is_default': True,
            'order': 4
        }
    )

def remove_events_app(apps, schema_editor):
    App = apps.get_model('portal', 'App')
    App.objects.filter(app_id='events').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('portal', '0007_userprofile_api_access_enabled_and_more'),
        ('events', '0001_initial')
    ]
    
    operations = [
        migrations.RunPython(create_events_app),
    ]
