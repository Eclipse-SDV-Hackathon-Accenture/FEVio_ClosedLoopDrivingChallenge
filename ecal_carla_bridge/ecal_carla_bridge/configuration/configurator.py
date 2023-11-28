import os
import yaml
from . import compose_schema

class Configurator():
    def __init__(self, config_compose_path):
        self.compose_config = self.load_config(config_compose_path)
        compose_schema.compose_schema.validate(self.compose_config)        

    def load_config(self, path):
        config = None
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError as e:
            print(e)
            exit()
        return config