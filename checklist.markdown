 SMOLKRAFT INTEGRATION CHECKLIST
 Changes required inside the `backend_api` app before / during the move
# 1. Move the db_router into the app

  Copy db_router.py (provided separately) into:
    backend_api/db_router.py

  The router references app_label = 'backend_api', which must match
  the AppConfig.name in backend_api/apps.py.
# 2. backend_api/apps.py — confirm app label

  Make sure it reads:

    class BackendApiConfig(AppConfig):
        default_auto_field = 'django.db.models.BigAutoField'
        name = 'backend_api'

  If the name is something else (e.g. 'smolkraft'), update the
  APP_LABEL constant in db_router.py to match.
# 3. Strip standalone auth from backend_api

  DELETE or stub out any of these if they exist in backend_api/urls.py:
    - login  view / path
    - logout view / path
    - register view / path
    - password reset views

  The portal's LoginRequiredMiddleware already enforces auth globally.
  Any unauthenticated request to /smolkraft/* will be redirected to
  portal:login automatically — no code needed in backend_api.
# 4. Update LoginRequiredMiddleware for any Smolkraft public routes

  If backend_api has routes that should be publicly accessible
  (e.g. a vendor-facing page, webhook endpoint), add their URL names
  to the public_urls list in roby_data_portal/middleware.py:

    self.public_urls = [
        ...existing entries...
        'backend_api:your_public_view_name',
    ]
# 5. Cross-database user references in backend_api models

  Because backend_api lives on a separate database, it CANNOT use a
  real ForeignKey to auth.User (different DB = no DB-level join).

  Anywhere in backend_api/models.py that currently has:
    user = models.ForeignKey(User, ...)

  Replace with:
    user_id = models.IntegerField(db_index=True)

  Then in views, look up the user from the portal DB when needed:
    from django.contrib.auth.models import User
    user = User.objects.get(id=request.user.id)   # hits default DB

  NOTE: This is the main structural change required. Everything else
  is plumbing.
# 6. ActivityLog integration (optional but recommended)

  To log Smolkraft activity in the portal's unified ActivityLog, add
  a helper to backend_api (e.g. backend_api/utils.py):

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

  Call this from your views wherever significant actions occur.
# 7. Register Smolkraft in the portal App table

  Either via a data migration or the Django admin, create an App row:
    app_id          = 'smolkraft'
    name            = 'Smolkraft'
    description     = '...'
    icon            = 'fa-...'
    background_color= '#...'
    link            = '/smolkraft/'
    is_default      = False   (or True if all users should see it)
    order           = <whatever fits in your dashboard>
# 8. Run migrations in order

  python manage.py migrate                          # default DB
  python manage.py migrate --database=smolkraft     # smolkraft DB

  The router ensures each migration only runs on the right database.

# 9. Smolkraft's own tests

  Any test that uses the default test database setup will need:
    databases = ['default', 'smolkraft']
  added to the TestCase class, or use:
    @override_settings(DATABASES={...})
  if running tests in isolation.