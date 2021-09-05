import logging
import os
import shutil
import tempfile
from zipfile import ZipFile

from download_data_from_prod.containers import Containers
from download_data_from_prod.ftp import download_sas_files
from helpers.config import load_config


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

    containers.run_db_cmds()
    containers.start_all_but_db()
