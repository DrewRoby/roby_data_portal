# portal/migrations/0003_add_default_apps.py

from django.db import migrations

def create_default_apps(apps, schema_editor):
    App = apps.get_model('portal', 'App')
    
    # Create default apps
    default_apps = [
        {
            'app_id': 'storycraft',
            'name': 'Storycraft',
            'description': 'Create and manage your stories, characters, and plots',
            'icon': 'fa-book',
            'background_color': '#4CAF50',
            'link': '/storycraft/',
            'is_default': True,
            'order': 1
        },
        {
            'app_id': 'schemascope',
            'name': 'Schema Navigator',
            'description': 'Analyze and track schemas from data files',
            'icon': 'fa-table',
            'background_color': '#2196F3',
            'link': '/schemascope/',
            'is_default': True,
            'order': 2
        },
        {
            'app_id': 'todo',
            'name': 'ToDo',
            'description': 'Manage your tasks and to-do lists',
            'icon': 'fa-check-square',
            'background_color': '#FF9800',
            'link': '/todo/',
            'is_default': True,
            'order': 3
        }
    ]
    
    for app_data in default_apps:
        App.objects.create(**app_data)

def remove_default_apps(apps, schema_editor):
    App = apps.get_model('portal', 'App')
    App.objects.filter(is_default=True).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('portal', '0002_create_app_models'),
    ]
    
    operations = [
        migrations.RunPython(create_default_apps, remove_default_apps),
    ]