import logging
import re

from compose.cli.command import get_project


class Containers:
    def __init__(self, project):
        self.project = project
        self._containers = []

    @property
    def containers(self):
        if not self._containers:
            project = get_project(self.project)
            self._containers = project.containers(stopped=True)
        return self._containers

    def get_container(self, service):
        for c in self.containers:
            if c.service == service:
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

    def is_running(self, service):
        if not self.containers:
            return False
        if not (container := self.get_container(service)):
            return False
        return container.is_running

    def run_cmds(self, service, cmds):
        logging.info("Commands execution ...")
        container = self.get_container(service)
        for cmd in cmds:
            result = self._exec_cmd(container, cmd)
            if result:
                logging.info(result)
        logging.info("... success")

    def restart_all(self):
        for c in self.containers:
            logging.info("Restart %s", c.service)
            c.restart()

    def stop_all(self):
        for c in self.containers:
            logging.info("Stop %s", c.service)
            c.stop()

    def restart(self, service):
        for c in self.containers:
            if c.service == service:
                logging.info("Restart %s", c.service)
                c.restart()
