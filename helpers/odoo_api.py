import os
import ssl
import xmlrpc.client

CONTEXT = os.getenv("NO_SSL")


class OdooAPI:
    """Class to handle  Odoo API requests."""

    def __init__(self, url, db, user, passwd):
        """Initialize xmlrpc connection."""
        try:
            self.url = url
            self.db = db
            self.user = user
            self.passwd = passwd
            common_proxy_url = "{}/xmlrpc/2/common".format(self.url)
            object_proxy_url = "{}/xmlrpc/2/object".format(self.url)
            context = ssl._create_unverified_context() if CONTEXT else None
            self.common = xmlrpc.client.ServerProxy(
                common_proxy_url,
                context=context,
            )
            self.uid = self.common.authenticate(
                self.db, self.user, self.passwd, {}
            )
            self.models = xmlrpc.client.ServerProxy(
                object_proxy_url,
                context=context,
            )
        except:  # noqa E722
            print("Impossible d'initialiser la connexion API Odoo")
            raise

    def get_entity_fields(self, entity):
        fields = self.models.execute_kw(
            self.db,
            self.uid,
            self.passwd,
            entity,
            "fields_get",
            [],
            {"attributes": ["string", "help", "type"]},
        )
        return fields

    def search_count(self, entity, cond=None):
        if cond is None:
            cond = []
        """Return how many lines are matching the request."""
        return self.models.execute_kw(
            self.db, self.uid, self.passwd, entity, "search_count", [cond]
        )

    def search_read(
        self,
        entity,
        cond=None,
        fields=None,
        limit=3500,
        offset=0,
        order="id ASC",
    ):
        """Main api request, retrieving data according search conditions."""
        if cond is None:
            cond = []
        if fields is None:
            fields = {}
        fields_and_context = {
            "fields": fields,
            "context": {"lang": "fr_FR", "tz": "Europe/Paris"},
            "limit": limit,
            "offset": offset,
            "order": order,
        }

        return self.models.execute_kw(
            self.db,
            self.uid,
            self.passwd,
            entity,
            "search_read",
            [cond],
            fields_and_context,
        )

    def update(self, entity, ids, fields):
        """Update entities which have ids, with new fields values."""
        return self.models.execute_kw(
            self.db, self.uid, self.passwd, entity, "write", [ids, fields]
        )

    def create(self, entity, fields):
        """Create entity instance with given fields values."""
        return self.models.execute_kw(
            self.db, self.uid, self.passwd, entity, "create", [fields]
        )

    def execute(self, entity, method, ids, params=None):
        if params is None:
            params = {}
        return self.models.execute_kw(
            self.db, self.uid, self.passwd, entity, method, [ids], params
        )

    def authenticate(self, login, password):
        return self.common.authenticate(self.db, login, password, {})
