import logging
import os
import shutil
import tempfile
from logging.handlers import RotatingFileHandler
from zipfile import ZipFile

from dotmap import DotMap
from ruamel.yaml import YAML

from containers import Containers
from ftp import download_sas_files

CONFIG_FILE = "config.yml"

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


def load_config():
    yaml = YAML(typ="safe")
    with open(CONFIG_FILE) as f:
        return DotMap(yaml.load(f), _dynamic=False)


def recursive_change_mod(path, mod):
    for dir_path, _, filenames in os.walk(path):
        os.chmod(dir_path, mod)
        for filename in filenames:
            os.chmod(os.path.join(dir_path, filename), mod)


def recursive_change_owner(path, user, group):
    for dir_path, _, filenames in os.walk(path):
        shutil.chown(dir_path, user=user, group=group)
        for filename in filenames:
            shutil.chown(
                os.path.join(dir_path, filename), user=user, group=group
            )


def main():
    config = load_config()

    filename = download_sas_files(config)
    if not filename:
        return

    containers = Containers(config)
    if not containers.is_db_running():
        logging.error("db is not running")
        return

    containers.stop_all_but_db()
    containers.restart_db()

    with tempfile.TemporaryDirectory() as tmp_dir:
        logging.info("Unzip from %s", filename)
        with ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        dump_path = os.path.join(config.db.dest, "dump.sql")
        shutil.rmtree(dump_path, ignore_errors=True)
        shutil.move(f"{tmp_dir}/dump.sql", dump_path)
        os.chmod(dump_path, config.db.mod)

        tmp_filestore = os.path.join(tmp_dir, "filestore")
        shutil.rmtree(config.odoo.dest, ignore_errors=True)
        shutil.move(tmp_filestore, config.odoo.dest)
        recursive_change_mod(
            config.odoo.dest,
            config.odoo.mod,
        )
        recursive_change_owner(
            config.odoo.dest,
            config.odoo.user,
            config.odoo.group,
        )

    containers.run_db_cmds()
    containers.start_all_but_db()


if __name__ == "__main__":
    main()
