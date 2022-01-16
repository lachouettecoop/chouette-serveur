import logging
import sys
from logging.handlers import RotatingFileHandler

from customers_populate_from_ldap import main as customers_populate_from_ldap
from download_data_from_prod import main as download_data_from_prod
from update_meal_voucher_products import main as update_meal_voucher_products

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
s_handler = logging.StreamHandler()
s_handler.setFormatter(formatter)
logger.addHandler(s_handler)
f_handler = RotatingFileHandler(
    filename="chouette-serveur.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=10,
    encoding="utf-8",
)
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)

if __name__ == "__main__":
    if len(sys.argv) <= 1 or sys.argv[1] == "download_data_from_prod":
        download_data_from_prod()
    elif sys.argv[1] == "update_meal_voucher_products":
        update_meal_voucher_products()
    elif sys.argv[1] == "customers_populate_from_ldap":
        customers_populate_from_ldap()
    sys.exit(-1)
