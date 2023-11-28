# Project Overview

The ecal-carla-bridge is an application which can be configured to publish sensor data gathered in Carla to eCAL topics and subscribe to topics that contain car instructions which are automaticaly applied to the corresponding Carla vehicle.


# Before you begin

Before you begin, make sure to install python version 3.7, eCAL and the eCAL python api. 

For the eCAL installation, please refer to the eCAL docs at https://eclipse-ecal.github.io/ecal/ .

**Python3.7**

Python3.7 for Windows:

A python 3.7 installer can be found at https://www.python.org/downloads/release/python-376/

Python3.7 for Linux:

```bash
$sudo apt-get -y install python3.7-dev python3.7-venv
$python3.7 -m ensurepip
```

**eCAL python api:**

Please visit https://github.com/eclipse-ecal/ecal/releases/tag/v5.12.1 and download the wheel file which matches your operating system and python version.

install pyton api Windows:

```powershell
py -V:3.7 pip install <filename>.whl
```

install python api Linux: 

```bash
python3.7 -m pip install <filename>.whl
```

# ecal-carla-bridge

The ecal-carla-bridge enables automated publishing of carla data to eCAL and subscribing to the corresponding instruction topics. The publishing of the
carla data includes sensor and transform data.

**Bridge setup**

install required dependencys with the requirements.txt file located in project_root/ecal-carla-bridge .

install requirements.txt Windows:

```powershell
py -V:3.7 -m pip install -r requirements.txt
```

install requirements.txt Linux:
```bash
python3.7 -m pip install -r requirements.txt
```

**Spawn actors into the Simulation:**

To use the ecal-carla-bridge, you need to spawn actors into the carla simulation.
The Bridge will automatically detect those new actors and publish the sensor data to eCAL topics. 

Note: The sensor needs to be configured before the bridge will enable publishing for this sensor.

**Configuration:**
To configure a sensor, you need to create a <>.yml file in the project_root/ecal-carla-bridge/config/car_configs folder. A possible configuration file could look like this:

```yaml
car_config:
    car_name: audi_a2
    car_instruction_topic: audi_a2_instructions 
    sensors:
      - config_key: fcc
        topic: FrontCenterCamera/Image
        publish: true
        algorithm: manual_drive
        type: camera.rgb
        convert_module:
          module_name: image_conversion
          convert_function: image_to_message
          message_type_function: get_message_type
```

The **car_name** field is mandatory to assign a configuration to a carla vehicle. For the configuration to be applied, the corresponding
carla vehicle needs the "role_name" attribute to be set to <car_name>. The "role_name" attribute can be set like:

```python
vehicle_blueprint = world.get_blueprint_library().find('vehicle.audi.a2')
vehicle_blueprint.attributes['role_name'] = audi_a2
```

The **car_instruction_topic** is the name of the topic for which the bridge creates a subscriber to receive instructions for the vehicle.

**sensors** is a list of sensor configurations for the car. A sensor configuration needs a config_key, which is similar to the car_name. The corresponding sensor
needs "role_name" to be set to  <config_key>:

```python
sensor_blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
sensor_blueprint.attributes['role_name'] = fcc
```

**publish** enables and disables the publishing of the sensor data.

**algorithm** might be removed soon, but it is still mandatory for the validation of the configuration.

**type** tells the bridge, which message type and message build function should be used. Valid types are the last two segments of a type_id 
(full type_id: sensor.camera.rgb, valid type: camera.rgb)

**convert_module** is recommended but not mandatory. The information grants access to a user generated conversion module. The conversion module is imported by its module_name. The Bridge looks in the project_root/carla-ecal-bridge directory for a module which matches the module name (make sure that your conversion modules are located in the src directory of the project). The conversion module has to implement a function, which takes the carla sensor data and generates a message from it and a function which returns the message type used to publish the sensor data. The convert_function field contains the name of the carla sensor data to message function without parenthesis and the message_type_function field contains the name of the get message type function without parantehesis.

note: If the config.yml does not contain a convert_module field the type field determines which conversion function and which message type is used.

To create a whole configuration with multiple car configurations a config_compose.yaml is needed in the project_root/ecal-carla-bridge/config directory: 

```yaml
configs:
  config_file_names: [audi_a2, <another file>]
```  
  
**config_file_names** are the files which should be included in your configuration. The bridge will look up these files in the project_root/ecal-carla-bridge/config/car_configs directory.

**Start the bridge:**
    
The bridge needs to be startet with py version 3.7 .

start bridge Windows:

```powershell
py -V:3.7 -m carla_ecal_bridge.main [args]
```

start bridge Linux:

```bash
python3.7 -m carla_ecal_bridge.main [args]
```

args:

```
--ip Default='localhost' "The ip address the carla simulation is running on"
--port Default='2000' "The port which the carla simulation is listening on"
--compose Default='ecal_carla_bridge/config/config_compose.yml' "The path to the desired config_compose file"
```

