import logging
import os
from datetime import datetime, timedelta
from ftplib import FTP

from helpers.config import load_config
from helpers.odoo_api import OdooAPI

ARTI_PREFIX = "ARTI_MAG_0000_"
TEXT_PREFIX = "TEXT_MAG_0000_"
SUFFIX = ".CSV"
WINDOWS_LINE_ENDING = "\r\n"
UNIX_LINE_ENDING = "\n"

config = load_config(__name__)
odoo_api = OdooAPI(
    config.odoo.url,
    config.odoo.db,
    config.odoo.user,
    config.odoo.password,
)


def get_logs():
    return odoo_api.search_read(
        entity="product.scale.log",
        cond=[
            ["sent", "=", False],
        ],
        fields=[
            "external_text",
            "product_text",
            "sent",
        ],
    )


def set_logs_as_sent(ids):
    odoo_api.update(entity="product.scale.log", ids=ids, fields={"sent": True})


def main():
    logs = get_logs()
    if not logs:
        logging.info("Nothing to update")
        return
    now = datetime.now() + timedelta(minutes=5)
    date_time = now.strftime("%Y%m%d_%H%M%S")
    arti_file_name = f"{ARTI_PREFIX}{date_time}{SUFFIX}"
    with open(arti_file_name, "a") as f:
        f.write(
            "".join([e.get("product_text") for e in logs]).replace(
                UNIX_LINE_ENDING, WINDOWS_LINE_ENDING
            )
        )
    text_file_name = f"{TEXT_PREFIX}{date_time}{SUFFIX}"
    with open(text_file_name, "a") as f:
        f.write(
            "".join([e.get("external_text") for e in logs]).replace(
                UNIX_LINE_ENDING, WINDOWS_LINE_ENDING
            )
        )
    logging.info(f"Uploading files {arti_file_name} and {text_file_name}")
    with FTP(config.ftp.host, config.ftp.user, config.ftp.password) as ftp:
        with open(arti_file_name, "rb") as f:
            ftp.storbinary(f"STOR {arti_file_name}", f)
        with open(text_file_name, "rb") as f:
            ftp.storbinary(f"STOR {text_file_name}", f)

    set_logs_as_sent([e.get("id") for e in logs])
    os.remove(arti_file_name)
    os.remove(text_file_name)
