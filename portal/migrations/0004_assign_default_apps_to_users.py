from django.db import migrations

def assign_default_apps(apps, schema_editor):
    """Assign default apps to all existing users."""
    User = apps.get_model('auth', 'User')
    App = apps.get_model('portal', 'App')
    UserAppAccess = apps.get_model('portal', 'UserAppAccess')
    
    # Get all default apps
    default_apps = App.objects.filter(is_default=True)
    
    # Get all users
    users = User.objects.all()
    
    # Assign default apps to all users
    for user in users:
        for app in default_apps:
            UserAppAccess.objects.get_or_create(user=user, app=app)

def remove_default_app_assignments(apps, schema_editor):
    """Remove all app assignments (for reversing the migration)."""
    UserAppAccess = apps.get_model('portal', 'UserAppAccess')
    UserAppAccess.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('portal', '0003_add_default_apps'),
    ]
    
    operations = [
        migrations.RunPython(assign_default_apps, remove_default_app_assignments),
    ]