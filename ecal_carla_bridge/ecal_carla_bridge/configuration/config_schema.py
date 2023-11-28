from schema import Schema, Optional, Or
import yaml

conv_module_schema = {
    "module_name": str,
    "convert_function": str,
    "message_type_function": str
}

sensor_schema = {
    "config_key": str,
    "topic": str,
    "publish": bool,
    "algorithm": str,
    "type": str,
    Optional("convert_module"): Or(conv_module_schema, {}, None)
}

car_schema = {
    "car_name": str,
    "car_instruction_topic": str,
    "sensors": [sensor_schema]
}

ad_conv_module_schema = {
    "module_name": str,
    "message_type_function": str
}

ad_sensor_schema = {
    "publish": bool,
    "topic": str,
    "type": str,
    "convert_module": ad_conv_module_schema

} 

ad_schema = {
    "car_instruction_topic": str,
    "sensors": [ad_sensor_schema]
}

car_config = Schema({"car_config": car_schema})
ad_config = Schema({"ad_config": ad_schema})