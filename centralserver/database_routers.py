ARCHIVE_APPS = ('archive',)
DB_CONFIG = 'archive'

class CentralServerRouter(object):

    """
    Put all archive-specific data in a separate database
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label in ARCHIVE_APPS:
            return DB_CONFIG
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ARCHIVE_APPS:
            return DB_CONFIG
        return None

    def allow_syncdb(self, db, model):
        if db == DB_CONFIG:
            return model._meta.app_label in ARCHIVE_APPS
        elif model._meta.app_label in ARCHIVE_APPS:
            return False
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        From docs: If no router has an opinion (i.e. all routers return None),
        only relations within the same database are allowed.
        """
        return None
