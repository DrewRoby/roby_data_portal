# smolkraft/db_router.py

class SmolkraftRouter:
    """
    Routes all smolkraft (sk_backend_api) app database operations to the
    'smolkraft' database, and keeps everything else on 'default'.

    To use, add to settings.py:
        DATABASE_ROUTERS = ['smolkraft.db_router.SmolkraftRouter']
    """

    APP_LABEL = 'sk_backend_api'
    DB_ALIAS = 'smolkraft'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.APP_LABEL:
            return self.DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.APP_LABEL:
            return self.DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between smolkraft and portal models are not allowed at the
        database level (they live on different DBs). Cross-app references must
        be handled in Python (e.g. storing user.id as an IntegerField, not a FK).
        """
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if self.APP_LABEL in labels and len(labels) > 1:
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.APP_LABEL:
            return db == self.DB_ALIAS
        if db == self.DB_ALIAS:
            return False
        return None
