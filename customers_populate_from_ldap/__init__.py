import logging
import sys

import ldap
import yaml

from helpers.config import load_config
from helpers.odoo_api import OdooAPI

"""
Update the list of Odoo customers (contacts stored in res.partner table)
from the list of person in a LDAP directory using their associated
barcode as matching key.
"""


def ldap_person_to_odoo_customer(ldap_person):
    """Extract variable name, barcode, email"""
    return {
        "name": f"{ldap_person['description'][0].decode('utf-8')} "
        f"{ldap_person['sn'][0].decode('utf-8')}",
        "barcode": ldap_person["homeDirectory"][0].decode("utf-8"),
        "email": ldap_person["mail"][0].decode("utf-8"),
        "active": True,
        "customer": True,
        "is_company": False,
    }


def update_odoo_customers(odoo, new_customers, dry_run=False):
    fields = list(new_customers[0].keys())

    old_customers = get_odoo_customers(odoo, fields)

    old_customers_dict = {
        customer["barcode"]: customer for customer in old_customers
    }
    new_customers_dict = {
        customer["barcode"]: customer for customer in new_customers
    }

    create_or_update_odoo_new_customers(
        odoo, old_customers_dict, new_customers_dict, dry_run
    )
    deactivate_odoo_old_customers(
        odoo, old_customers_dict, new_customers_dict, dry_run
    )


def get_odoo_customers(odoo, fields):
    # We need to search explicitly for additional active=False items because
    # they are filtered out by default.
    return odoo.search_read(
        entity="res.partner",
        cond=[
            ["is_company", "=", False],
            ["customer", "=", True],
            ["active", "=", True],
        ],
        fields=fields,
    ) + odoo.search_read(
        entity="res.partner",
        cond=[
            ["is_company", "=", False],
            ["customer", "=", True],
            ["active", "=", False],
        ],
        fields=fields,
    )


def create_or_update_odoo_new_customers(
    odoo, old_customers_dict, new_customers_dict, dry_run=False
):
    for barcode, new_cstmr in new_customers_dict.items():
        if not barcode:
            logging.info(
                f"# LDAP person without barcode: {new_cstmr['name']}, {new_cstmr['email']}",
            )
        if barcode not in old_customers_dict:
            logging.info(
                f"+ create customer: {new_cstmr['name']}, {new_cstmr['email']}",
            )
            if not dry_run:
                odoo_id = odoo.create(
                    entity="res.partner",
                    fields=new_cstmr,
                )
                logging.info(f"    => id: {odoo_id}")
        else:
            old_cstmr = old_customers_dict[barcode]
            differences = {
                field: value
                for field, value in new_cstmr.items()
                if old_cstmr[field] != value
            }
            if differences:
                logging.info(
                    f"! update customer {old_cstmr['id']} {old_cstmr['name']} set {differences}"
                )
                if not dry_run:
                    odoo.update(
                        entity="res.partner",
                        ids=[old_cstmr["id"]],
                        fields=differences,
                    )


def deactivate_odoo_old_customers(
    odoo, old_customers_dict, new_customers_dict, dry_run=False
):
    for barcode, old_cstmr in old_customers_dict.items():
        if not barcode:
            logging.info(
                f"# Odoo customer without barcode: {old_cstmr['id']}, "
                f"{old_cstmr['name']}, {old_cstmr['email']}"
            )
        elif barcode not in new_customers_dict and old_cstmr["active"]:
            logging.info(
                f"- deactivate customer: {old_cstmr['id']}, "
                f"{old_cstmr['name']}, {old_cstmr['email']}"
            )
            if not dry_run:
                odoo.update(
                    entity="res.partner",
                    ids=[old_cstmr["id"]],
                    fields={"active": False},
                )


def search_ldap_persons(url, dn, user, password):
    # Connect to ldap server
    ldp = ldap.initialize(url)
    ldp.protocol_version = ldap.VERSION3
    ldp.simple_bind_s(user, password)
    return [
        person
        for _, person in ldp.search_s(
            dn, ldap.SCOPE_SUBTREE, "(objectClass=person)"
        )
    ]


# Parses Configuration file and returns variables from that file
def open_conf_file(filename):
    """Open and return the content of the .yml configuration file.
    check that the required fields are present.
    """
    conf = yaml.load(open(filename))
    for section, fields in {
        "ldap": ["url", "username", "password", "dn"],
        "odoo": ["url", "db", "username", "password"],
    }.items():
        if section not in conf:
            logging.error(f"missing section «{section}:» in {filename}")
            sys.exit(-1)
        else:
            fields = set(fields)
            actual_fields = set(conf[section].keys())
            for field in fields - actual_fields:
                logging.error(
                    f"missing field «{field}:» in section «{section}:» of file {filename}"
                )
                sys.exit(-1)
            for field in actual_fields - fields:
                logging.error(
                    f"unknown field «{field}:» in section «{section}:» of file {filename}"
                )
                sys.exit(-1)
    return conf


def main():
    config = load_config(__name__)
    ldap_persons = search_ldap_persons(**config["ldap"])
    odoo_api = OdooAPI(
        config.odoo.url,
        config.odoo.db,
        config.odoo.user,
        config.odoo.password,
    )
    new_customers = [ldap_person_to_odoo_customer(p) for p in ldap_persons]
    update_odoo_customers(
        odoo_api,
        new_customers,
    )
