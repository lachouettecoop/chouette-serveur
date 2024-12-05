import logging

import subprocess


class Containers:
    def __init__(self, project):
        self.project = project
        self._containers = []

    def restart_all(self):
        try:
            # Run `docker-compose up`
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project,
                check=True)
            logging.info(f"Docker Compose started successfully for {self.project}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running docker-compose: {e}")

    def restart(self, container):
        try:
            # Run `docker-compose up`
            subprocess.run(
                ["docker-compose", "up", "-d", container],
                cwd=self.project,
                check=True)
            logging.info(f"{container} started successfully for {self.project}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running docker-compose: {e}")

    def stop_all(self):
        try:
            # Run `docker-compose down`
            subprocess.run(
                ["docker-compose", "stop"],
                cwd=self.project,
                check=True
            )
            logging.info(f"Docker Compose stopped for {self.project}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error stopping docker-compose: {e}")

    def run_cmds(self, container, cmds):
        for cmd in cmds:
            try:
                # Run `docker-compose down`
                subprocess.run(
                    ["docker-compose", "exec", container, cmd],
                    cwd=self.project,
                    check=True
                )
                logging.info(f"Docker Compose run cmd for {self.project}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error run cmd docker-compose: {e}")
