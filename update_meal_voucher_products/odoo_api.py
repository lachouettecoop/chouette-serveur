import os
import xmlrpc.client

ODOO_URL = os.getenv("ODOO_URL", "https://sas.lachouettecoop.fr")
ODOO_DB = os.getenv("ODOO_DB", "dbsas")
ODOO_LOGIN = os.getenv("ODOO_LOGIN")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")


class OdooAPI:
    """Class to handle  Odoo API requests."""

    def __init__(self):
        """Initialize xmlrpc connection."""
        try:
            common_proxy_url = f"{ODOO_URL}/xmlrpc/2/common"
            object_proxy_url = f"{ODOO_URL}/xmlrpc/2/object"
            self.common = xmlrpc.client.ServerProxy(common_proxy_url)
            self.uid = self.common.authenticate(
                ODOO_DB, ODOO_LOGIN, ODOO_PASSWORD, {}
            )
            self.models = xmlrpc.client.ServerProxy(object_proxy_url)
        except Exception:
            print("Impossible d'initialiser la connexion API Odoo")

    def get_entity_fields(self, entity):
        fields = self.models.execute_kw(
            ODOO_DB,
            self.uid,
            ODOO_PASSWORD,
            entity,
            "fields_get",
            [],
            {"attributes": ["string", "help", "type"]},
        )
        return fields

    def search_count(self, entity, cond=None):
        """Return how many lines are matching the request."""
        if cond is None:
            cond = []
        return self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, entity, "search_count", [cond]
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
        if fields is None:
            fields = {}
        if cond is None:
            cond = []
        fields_and_context = {
            "fields": fields,
            "context": {"lang": "fr_FR", "tz": "Europe/Paris"},
            "limit": limit,
            "offset": offset,
            "order": order,
        }

        return self.models.execute_kw(
            ODOO_DB,
            self.uid,
            ODOO_PASSWORD,
            entity,
            "search_read",
            [cond],
            fields_and_context,
        )

    def update(self, entity, ids, fields):
        """Update entities which have ids, with new fields values."""
        return self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, entity, "write", [ids, fields]
        )

    def create(self, entity, fields):
        """Create entity instance with given fields values."""
        return self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, entity, "create", [fields]
        )

    def execute(self, entity, method, ids, params=None):
        if params is None:
            params = {}
        return self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, entity, method, [ids], params
        )

    def authenticate(self, login, password):
        return self.common.authenticate(ODOO_DB, login, password, {})
