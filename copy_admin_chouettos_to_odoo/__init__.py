import logging

from helpers.config import CONFIG
from helpers.containers import Containers

from .db_converter import parse

DUMP_FILE = "adminchouettos.sql"
TABLE_NAMES = [
    "adhesion",
    "adresse",
    "creneau",
    "creneau_generique",
    "doctrine_migration_versions",
    "fos_user",
    "paiement",
    "personne",
    "personne_rattachee",
    "piaf",
    "poste",
    "reserve",
    "reserve_creneau_generique",
    "role",
    "statut",
    "user_adresse",
    "user_role",
]


def main():
    config = CONFIG.get(__name__)

    logging.info("dump admin_chouettos")
    containers = Containers(config.admin_chouettos.path)
    db = containers.get_container(config.admin_chouettos.db)
    user = db.environment["MARIADB_USER"]
    password = db.environment["MARIADB_PASSWORD"]
    database = db.environment["MARIADB_DATABASE"]
    dump_cmd = (
        "mysqldump --compatible=postgresql --default-character-set=utf8 "
        f"-u {user} -p{password} {database} > /var/lib/mysql/{DUMP_FILE}"
    )
    containers.run_cmds(
        config.admin_chouettos.db,
        [f"sh -c '{dump_cmd}'"],
    )

    with open(
        f"{config.admin_chouettos.path}/{config.admin_chouettos.data_path}/{DUMP_FILE}",
        "r",
    ) as file:
        data = file.read()
    for table_name in TABLE_NAMES:
        data = data.replace(f'"{table_name}"', f'"adminc_{table_name}"')
    temp_sql = f"{config.odoo.path}/{config.odoo.data_path}/{DUMP_FILE}.tmp"
    with open(temp_sql, "w") as file:
        file.write(data)
    odoo_sql = f"{config.odoo.path}/{config.odoo.data_path}/{DUMP_FILE}"
    parse(temp_sql, odoo_sql)

    logging.info("drop/create/insert in odoo")
    containers = Containers(config.odoo.path)
    db = containers.get_container(config.odoo.db)
    user = db.environment["POSTGRES_USER"]
    database = db.environment["POSTGRES_DB"]
    dump_cmd = (
        f"psql -U {user} {database} < /var/lib/postgresql/data/{DUMP_FILE}"
    )
    containers.run_cmds(
        config.odoo.db,
        [f"sh -c '{dump_cmd}'"],
    )
