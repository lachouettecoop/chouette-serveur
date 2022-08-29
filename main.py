import logging
import sys
from logging.handlers import RotatingFileHandler

import sentry_sdk

from helpers.config import CONFIG

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

if sentry_config := CONFIG.get("sentry"):
    sentry_sdk.init(dsn=sentry_config.dsn, traces_sample_rate=1.0)

if __name__ == "__main__":
    if len(sys.argv) <= 1 or sys.argv[1] == "download_data_from_prod":
        from download_data_from_prod import main

    elif sys.argv[1] == "update_meal_voucher_products":
        from update_meal_voucher_products import main

    elif sys.argv[1] == "customers_populate_from_ldap":
        from customers_populate_from_ldap import main

    elif sys.argv[1] == "update_scales":
        from update_scales import main

    elif sys.argv[1] == "copy_admin_chouettos_to_odoo":
        from copy_admin_chouettos_to_odoo import main

    main()
    sys.exit(-1)
