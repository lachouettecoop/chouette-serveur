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


def exec_cmd(container, cmd):
    logging.info("Execute '%s' in docker %s", cmd, container.name)
    exec_id = container.create_exec(cmd)
    result = container.start_exec(exec_id)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result


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
    containers = project.containers()

    if not containers or "db" not in [c.service for c in containers]:
        logging.error("db is not running")
        return

    db_container = None
    for c in containers:
        if c.service != "db":
            logging.info("Stopping %s", c.service)
            c.stop()
        else:
            db_container = c

    if not db_container:
        logging.info("db has been stopped")

    logging.info("Restore DB ...")
    for cmd in config.compose.cmds:
        result = exec_cmd(db_container, cmd)
        if result:
            logging.info(result)
    logging.info("... success")

    for c in containers:
        if c.service != "db":
            logging.info("Restart %s", c.service)
            c.start()


if __name__ == "__main__":
    main()
