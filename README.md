# chouette-serveur
Script pour automatiser l'administration du serveur

### Installation
```shell
poetry install
```

### Configuration
Creer un fichier config.yml contenant :
```yaml
ftp:
  host: ...         # FTP host
  user: ...         # Username
  password: ...     # Password
  backups_pass: ... # From where the zip is download

db:
  dest: ..          # Where the dump.sql is unziped
  mod: 0o775        # chmod dump.sql

odoo:
  dest:             # Where the files are unziped
  mod: 0o775        # chmod files
  user: 104         # chown files
  group: 107        # chown files

compose:
  project: ...      # Project path with docker_compose.yml
  db_cmds:          # List of commands to execute in db docker
  - dropdb -U odoo dbsas
  - createdb -U odoo dbsas
  - sh -c 'psql -U odoo -d dbsas < /var/lib/postgresql/data/dump.sql'
  - sh -c 'psql -U odoo -d dbsas -c "UPDATE ir_cron SET active = false;"'
  - vacuumdb -U odoo -a
```

### Execution
```shell
poetry run python mail.py
```
