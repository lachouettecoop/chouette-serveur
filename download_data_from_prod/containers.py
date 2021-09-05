import logging
import re

from compose.cli.command import get_project


class Containers:
    def __init__(self, config):
        self.config = config
        self._containers = []

    @property
    def containers(self):
        if not self._containers:
            project = get_project(self.config.compose.project)
            self._containers = project.containers()
        return self._containers

    @property
    def db_container(self):
        for c in self.containers:
            if c.service == "db":
                return c

    @staticmethod
    def _exec_cmd(container, cmd):
        logging.info('Execute "%s" in docker %s', cmd, container.name)
        exec_id = container.create_exec(cmd)
        result = container.start_exec(exec_id)
        if isinstance(result, bytes):
            result = result.decode("utf-8")
        errors = []
        for line in result.splitlines():
            if line and re.search("error", line, re.IGNORECASE):
                errors.append(line)
        if errors:
            return "\n".join(errors)
        return "successful operation"

    def is_db_running(self):
        if not self.containers or not self.db_container:
            return False
        return True

    def run_db_cmds(self):
        logging.info("Restore DB ...")
        for cmd in self.config.compose.db_cmds:
            result = self._exec_cmd(self.db_container, cmd)
            if result:
                logging.info(result)
        logging.info("... success")

    def stop_all_but_db(self):
        for c in self.containers:
            if c.service != "db":
                logging.info("Stop %s", c.service)
                c.stop()

    def restart_db(self):
        for c in self.containers:
            if c.service == "db":
                logging.info("Restart %s", c.service)
                c.restart()

    def start_all_but_db(self):
        for c in self.containers:
            if c.service != "db":
                logging.info("Start %s", c.service)
                c.start()
