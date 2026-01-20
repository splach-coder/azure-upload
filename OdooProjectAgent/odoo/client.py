import xmlrpc.client

class OdooClient:
    def __init__(self, url: str, db: str, username: str, api_key: str):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self.uid = None
        self.models = None

    def authenticate(self):
        """Authenticate with Odoo and set up the models proxy."""
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.username, self.api_key, {})
        
        if not self.uid:
            raise Exception("Odoo Authentication Failed")
        
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return self.uid

    def create(self, model, values):
        """Create a new record."""
        if not self.uid:
            self.authenticate()
        return self.models.execute_kw(self.db, self.uid, self.api_key, model, 'create', [values])
