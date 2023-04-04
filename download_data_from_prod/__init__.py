import logging
import os
import shutil
import tempfile
from zipfile import ZipFile

from download_data_from_prod.ftp import download_sas_files
from helpers.config import CONFIG
from helpers.containers import Containers


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
    config = CONFIG.get(__name__)

    filename = download_sas_files(config)
    if not filename:
        return

    metabase_containers = Containers(config.compose.metabase)
    odoo_containers = Containers(config.compose.odoo)
    try:
        metabase_containers.stop_all()
        odoo_containers.stop_all()
        odoo_containers.restart("db")

        with tempfile.TemporaryDirectory() as tmp_dir:
            logging.info("Unzip from %s", filename)
            with ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            dump_path = os.path.join(config.containers.db.dest, "dump.sql")
            shutil.rmtree(dump_path, ignore_errors=True)
            shutil.move(f"{tmp_dir}/dump.sql", dump_path)
            os.chmod(dump_path, config.containers.db.mod)

            tmp_filestore = os.path.join(tmp_dir, "filestore")
            shutil.rmtree(config.containers.odoo.dest, ignore_errors=True)
            shutil.move(tmp_filestore, config.containers.odoo.dest)
            recursive_change_mod(
                config.containers.odoo.dest,
                config.containers.odoo.mod,
            )
            recursive_change_owner(
                config.containers.odoo.dest,
                config.containers.odoo.user,
                config.containers.odoo.group,
            )

        odoo_containers.run_cmds("db", config.compose.db_cmds)
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
    finally:
        odoo_containers.restart_all()
        metabase_containers.restart_all()
