import logging

from helpers.config import CONFIG
from helpers.odoo_api import OdooAPI
from update_meal_voucher_products.categories import MEAL_VOUCHER_CATEGORIES


def get_produts_that_should_be_mv(odoo_api):
    entities = odoo_api.search_read(
        entity="product.template",
        cond=[
            ["sale_ok", "=", True],
            ["meal_voucher_ok", "=", False],
            ["categ_id", "in", MEAL_VOUCHER_CATEGORIES],
        ],
        fields=["id", "name"],
    )
    return entities


def set_products_mv(odoo_api, entities):
    odoo_api.update(
        entity="product.template",
        ids=[p["id"] for p in entities],
        fields={"meal_voucher_ok": True},
    )


def main():
    config = CONFIG.get(__name__)
    odoo_api = OdooAPI(
        config.odoo.url,
        config.odoo.db,
        config.odoo.user,
        config.odoo.password,
    )
    entities = get_produts_that_should_be_mv(odoo_api)
    if entities:
        set_products_mv(odoo_api, entities)
        logging.info(f"{len(entities)} products have been updated")
    else:
        logging.info("No product to update")
