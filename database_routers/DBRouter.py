class BuildingsRouter:
    """
    Buildings should share the same data in test and prod
    """
    route_app_labels = {"buildings"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read buildings models go to buildings_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "buildings_db"
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write buildings models go to buildings_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "buildings_db"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the buildings apps is
        involved.
        """
        if (
                obj1._meta.app_label in self.route_app_labels or
                obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the buildings app only appears in the
        "buildings_db" database.
        """
        if app_label in self.route_app_labels:
            return db == "buildings_db"
        return None
