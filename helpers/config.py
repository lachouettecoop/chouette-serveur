from dotmap import DotMap
from ruamel.yaml import YAML

CONFIG_FILE = "config.yml"


def load_config():
    yaml = YAML(typ="safe")
    with open(CONFIG_FILE) as f:
        return DotMap(yaml.load(f), _dynamic=False)


CONFIG = load_config()
