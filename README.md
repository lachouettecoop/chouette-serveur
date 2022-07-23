# chouette-serveur
Script pour automatiser l'administration du serveur

### Installation
```shell
poetry install
```

### Configuration
Creer un fichier config.yml en vous inspirant de config.yml.example

### Execution
```shell
poetry run python mail.py
```

### mysql to postgresql
This script comes from project : [mysql-postgresql-converter](https://github.com/machisuji/mysql-postgresql-converter/blob/master/db_converter.py)
Thanks to [machisuji](https://github.com/machisuji)

### Sauvegarde
Tous nos docker sont sauvegardés à intervalle régulier.
On utilise l'outil borg et la surcouche borgmatic.
Un bon tuto pour commencer : [https://lafor.ge/backup/](https://lafor.ge/backup/). Merci [akanoa](https://gitlab.com/Akanoa) pour ce super article.

Pour initialiser le dossier de sauvegarde :
```shell
borg init -e none /mnt/disk/borg/coquecigrue-adminchouettos
```

Pour effectuer une sauvegarde, la commande est dans le crontab.
```shell
*/30 * * * * /usr/local/bin/borgmatic --log-file /var/log/chouette-backups.log --log-file-verbosity 1 -c /root/docker/chouette-admin-chouettos/borgmatic.yaml
```

Example de fichier de configuration :
```yaml
location:
  source_directories:
    - /root/docker/chouette-admin-chouettos
  repositories:
    - /mnt/disk/borg/coquecigrue-adminchouettos
storage:
  archive_name_format: '{hostname}-adminchouettos-{now:%Y-%m-%dT%H:%M}'
  unknown_unencrypted_repo_access_is_ok: true
  retries: 4
  retry_wait: 30
retention:
  prefix: '{hostname}-adminchouettos-'
  keep_daily: 12
  keep_weekly: 28
  keep_monthly: 10
```

Pour lister les sauvegardes :
```shell
borg list /mnt/disk/borg/coquecigrue-adminchouettos
coquecigrue-adminchouettos-2022-07-23T11:37 Sat, 2022-07-23 11:37:24 [ac120342a43b964b0a18a76b2481119ef39ae94196c82cc5a9412721d4fd3ad4]
...
```

Pour restaurer une sauvegarde :
```shell
borg export-tar --tar-filter="gzip -9" /mnt/disk/borg/coquecigrue-adminchouettos::coquecigrue-adminchouettos-2022-07-23T11:37 /tmp/adminchouettos.tar.gz
```

Il suffit de ensuite de decompresser le fichier `/tmp/adminchouettos.tar.gz`.
Il s'agit du dossier `/root/docker/chouette-admin-chouettos` à la date du `2022-07-23 11:37:24`.
