import glob
import logging
import os
from ftplib import FTP_TLS
from logging.handlers import RotatingFileHandler
from zipfile import ZipFile

from compose.cli.command import get_project
from dotmap import DotMap
from ruamel.yaml import YAML

CONFIG_FILE = "config.yml"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
s_handler = logging.StreamHandler()
s_handler.setFormatter(formatter)
logger.addHandler(s_handler)
f_handler = RotatingFileHandler(
    filename="chouette-serveur.log",
    maxBytes=1024,
    backupCount=3,
    encoding="utf-8",
)
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


def load_config():
    yaml = YAML(typ="safe")
    with open(CONFIG_FILE) as f:
        return DotMap(yaml.load(f), _dynamic=False)


def exec_cmd(container, cmd):
    logging.info("Execute '%s' in docker %s", cmd, container.name)
    exec_id = container.create_exec(cmd)
    return container.start_exec(exec_id)


def delete_old_zip():
    zip_files = glob.glob("*.zip")
    if len(zip_files) <= 1:
        return
    zip_files.sort()
    for filename in zip_files[:-1]:
        logging.info("Remove file %s", filename)
        os.remove(filename)


def main():
    config = load_config()

    delete_old_zip()

    ftp = FTP_TLS(
        host=config.ftp.host, user=config.ftp.user, passwd=config.ftp.password
    )
    ftp.cwd(config.ftp.backups_pass)
    ftp.set_pasv(True)

    ftp_files = []

    def add_file(file):
        ftp_files.append(file.split()[-1])

    ftp.retrlines("LIST", callback=add_file)

    ftp_files.sort()
    filename = ftp_files[-1]

    if not os.path.isfile(filename):
        logging.info("Download file %s", filename)
        with open(filename, "wb") as fp:
            ftp.retrbinary(f"RETR {filename}", fp.write)

    logging.info("Unzip dump.sql from %s", filename)
    with ZipFile(filename, "r") as zip_ref:
        zip_ref.extract("dump.sql", config.zip.destination)

    project = get_project(config.compose.project)
    containers = project.containers(service_names=["db"])

    if not containers:
        logging.error("db is not running")
        return
    db_container = containers[0]

    logging.info("Restore DB ...")
    for cmd in config.compose.cmds:
        exec_cmd(db_container, cmd)
    logging.info("... success")


if __name__ == "__main__":
    main()
