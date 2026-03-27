from portal.models import ActivityLog, App

def log_smolkraft_activity(user, activity_type, description):
    try:
        app = App.objects.get(app_id='smolkraft')
        ActivityLog.objects.create(
            user=user,
            app=app,
            activity_type=activity_type,
            description=description,
        )
    except App.DoesNotExist:
        pass  # Don't crash if the App row hasn't been created yet