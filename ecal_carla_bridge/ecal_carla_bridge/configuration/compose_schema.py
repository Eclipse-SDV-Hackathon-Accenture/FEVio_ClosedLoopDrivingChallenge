from schema import Schema, SchemaError, Or
import yaml

compose_config_schema = {
    "config_filenames": [str],
}

compose_schema = Schema({"configs": compose_config_schema})