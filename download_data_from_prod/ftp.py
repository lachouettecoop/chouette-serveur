import glob
import logging
import os
from ftplib import FTP_TLS


def _delete_old_zip():
    zip_files = glob.glob("*.zip")
    if len(zip_files) <= 1:
        return
    zip_files.sort()
    for filename in zip_files[:-1]:
        logging.info("Remove file %s", filename)
        os.remove(filename)


def download_sas_files(config, force=False):
    _delete_old_zip()

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

    if os.path.isfile(filename):
        logging.info("File %s already exists - Nothing to do", filename)
        return filename if force else None

    logging.info("Downloading file %s", filename)
    with open(filename, "wb") as fp:
        ftp.retrbinary(f"RETR {filename}", fp.write)

    return filename
