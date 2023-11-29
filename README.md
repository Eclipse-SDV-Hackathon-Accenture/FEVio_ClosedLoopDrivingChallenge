# ClosedLoopDrivingChallenge
SDV Hackathon repo for Closed loop CARLA challenge

# Prerequisites
- Ubuntu(preferred) or Windows environment
- RTX2070 GPU or above (preferred), if no GPU available then the CPU will be used with loss of performance as a result.
- X86 CPU is mandatory

# Required tools
- Carla simuator (https://carla.org/)
- Ecal_Carla_Bridge (https://github.com/eclipse-ecal/ecal-carla-bridge)
- ECAL (https://github.com/eclipse-ecal/ecal)
- Ecal_Foxglove_Bridge (https://github.com/eclipse-ecal/ecal-foxglove-bridge)
- Foxglove (https://foxglove.dev/download)
- GIT
- Python 3.x

**NOTE**: For many of the above tools there is need for dependencies. These dependencies can be installed by running the following command:

                pip install -r requirements.txt


# How to run the Traffic Jam Detection Telltale

Once all the required tools are installed we can start them and generate data out of the CARLA simulation and display a telltale indicating if a trafficJam is occuring for which the driver will be allerted to reduce velocity.

1. We can start by starting the **CARLA** simulator and verifying the world is loaded. 
2. Once the CARLA world is loaded we need to generate some traffic in order for our algorithm to detect cars, we can do this by running the **generate_traffic.py** script found at Scripts_Carla/generate_traffic.py
3. Once our simulation has cars driving around we can proceed by starting the **ecal_carla_bridge**. 
4. After the bridge is started we can start the detection algorithm by running **annotatee_images.py in the folder object_detection
5. Once the object detection algorithm is running we can start the ecal_foxglove_bridge
6. Last thing to do is to run foxglove, open the connection to the foxglove bridge websocket, open a new panel and subscribe to our topics. **note** We need to make sure to enable to annotation by clicken on the 'cogwheel' on the top right corner of our camera_panel, then at annotations  tab on the left side we need to click on the 'make visable' icon. We also need to add a panel for our telltale by adding a '

Great! If all went well we should now see the camera image from CARLA in Foxglove with the annotations over the detected cars. 



