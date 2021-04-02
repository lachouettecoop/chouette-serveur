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
  host: ... # FTP host
  user: ... # Username
  password: ... # Password
  backups_pass: ... # From where the zip is download

zip:
  destination: ... # To where the zip is download

compose:
  project: ... # Project path with docker_compose.yml
  cmds:
    - ...  # List of commands to execute in db docker
    - ...
```

### Execution
```shell
poetry run python mail.py
```