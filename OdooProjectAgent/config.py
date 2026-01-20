import os

class Config:
    # Odoo Settings
    ODOO_URL = os.getenv("ODOO_URL", "https://dkm-customs.odoo.com")
    ODOO_DB = os.getenv("ODOO_DB", "vva-onniti-dkm-main-20654023")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "anas.benabbou@dkm-customs.com")
    ODOO_API_KEY = os.getenv("ODOO_API_KEY", "d3f959e2b9dcca8d7180b95c8d673398b8b6040c")
