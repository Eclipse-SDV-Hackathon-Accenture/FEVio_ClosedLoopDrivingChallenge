import ros.sensor_msgs.Image_pb2 as img
import ros.sensor_msgs.PointCloud2_pb2 as pc
import ros.tf2_msgs.TFMessage_pb2 as trans
import ros.sensor_msgs.NavSatFix_pb2 as gnss
import ros.sensor_msgs.Imu_pb2 as imu

import sys
import os
import glob

from scipy.spatial.transform import Rotation

import carla

covariance = [0.01, 0, 0,
              0, 0.01, 0,
              0, 0, 0.01]

def rgb_image_to_message(rgb_image: carla.Image, frame_id):
        message = img.Image()

        message = set_header(message, rgb_image, frame_id)
        message.height = rgb_image.height
        message.width = rgb_image.width
        message.encoding = "bgra8"
        message.is_bigendian = 0
        message.step = 4 * rgb_image.width
        message.data = bytes(rgb_image.raw_data)

        return message

def semseg_image_to_message(semseg_image: carla.Image, frame_id):
    semseg_image.convert(carla.ColorConverter.CityScapesPalette)
    return rgb_image_to_message(semseg_image, frame_id)

def lidar_to_message(lidar_data: carla.LidarMeasurement, frame_id):
    message = pc.PointCloud2()

    message = set_header(message, lidar_data, frame_id)
    message.height = 1
    message.width = len(lidar_data)

    field = message.fields.add()

    field.name = "x"
    field.offset = 0
    field.datatype = 7
    field.count = 1

    field = message.fields.add()

    field.name = "y"
    field.offset = 4
    field.datatype = 7
    field.count = 1

    field = message.fields.add()

    field.name = "z"
    field.offset = 8
    field.datatype = 7
    field.count = 1
    
    field = message.fields.add()

    field.name = "intensity"
    field.offset = 12
    field.datatype = 7
    field.count = 1

    message.is_bigendian = 0
    message.point_step = 16
    message.row_step = 16*len(lidar_data)
    message.data = bytes(lidar_data.raw_data)

    return message

def transformations_to_message(trans_list):
    message = trans.TFMessage()

    for transform in trans_list:
        curr_trans = message.transforms.add()
        curr_trans.header.frame_id = transform[1]
        curr_trans.child_frame_id = transform[2]
        
        curr_trans.transform.translation.x = transform[0].location.x
        curr_trans.transform.translation.y = transform[0].location.y
        curr_trans.transform.translation.z = transform[0].location.z
        rot = Rotation.from_euler('xyz', [transform[0].rotation.roll, transform[0].rotation.pitch, transform[0].rotation.yaw], degrees=True)
        quaternion = rot.as_quat()
        curr_trans.transform.rotation.x = quaternion[0]
        curr_trans.transform.rotation.y = quaternion[1]
        curr_trans.transform.rotation.z = quaternion[2]
        curr_trans.transform.rotation.w = quaternion[3]
    
    return message

def gnss_to_message(data, frame_id):
    global covariance
    message = gnss.NavSatFix()

    message = set_header(message, data, frame_id)
    message.status.status = 0
    message.status.service = 1
    message.latitude = data.latitude
    message.longitude = data.longitude
    message.altitude = data.altitude
    message.position_covariance.extend(covariance)

    return message

def imu_to_message(data, frame_id):
    global covariance
    message = imu.Imu()

    message = set_header(message, data, frame_id)

    rot = Rotation.from_euler('y', data.compass, degrees=True)
    quaternion = rot.as_quat()

    message.orientation.x = quaternion[0]
    message.orientation.y = quaternion[1]
    message.orientation.z = quaternion[2]
    message.orientation.w = quaternion[3]

    message.orientation_covariance.extend(covariance)

    message.linear_acceleration.x = data.accelerometer.x
    message.linear_acceleration.y = data.accelerometer.y
    message.linear_acceleration.z = data.accelerometer.z

    message.linear_acceleration_covariance.extend(covariance)

    message.angular_velocity.x = data.gyroscope.x
    message.angular_velocity.y = data.gyroscope.y
    message.angular_velocity.z = data.gyroscope.z

    message.angular_velocity_covariance.extend(covariance)

    return message

def radar_to_message(data, frame_id):
    message = pc.PointCloud2()

    data_in = np.empty(len(data)*4, dtype=np.float32)
    count = 0
    for detection in data:
        data_in[count] = detection.altitude
        data_in[count+1] = detection.azimuth
        data_in[count+2] = detection.depth
        data_in[count+3] = detection.velocity
        count += 4

    raw_data_transformed = polar_to_cartesian(data_in)

    message = set_header(message, data, frame_id)
    message.height = 1
    message.width = len(data)

    field = message.fields.add()
     
    field.name = "x"
    field.offset = 0
    field.datatype = 7
    field.count = 1

    field = message.fields.add()
     
    field.name = "y"
    field.offset = 4
    field.datatype = 7
    field.count = 1

    field = message.fields.add()
     
    field.name = "z"
    field.offset = 8
    field.datatype = 7
    field.count = 1

    field = message.fields.add()

    field.name = "velocity"
    field.offset = 12
    field.datatype = 7
    field.count = 1

    message.is_bigendian = 0
    message.point_step = 16
    message.row_step = 16*len(data)
    message.data = bytes(raw_data_transformed)

    return message

def set_header(message, data, frame_id):
    try:
        message.header.stamp.sec = int(data.timestamp)
        message.header.stamp.nsec = int(data.timestamp %1 *1000 * 1000000)
        message.header.seq = data.frame
    except:
        pass
    message.header.frame_id = frame_id

    return message

import numpy as np


def polar_to_cartesian(data_in):
    float_array = data_in.reshape(-1,4)

    data_out = float_array.copy()
    
    data_out[:, 0] = float_array[:, 2] * np.cos(float_array[:, 0]) * np.cos(float_array[:, 1])
    data_out[:, 1] = -float_array[:, 2] * np.cos(float_array[:, 0]) * np.sin(float_array[:, 1])
    data_out[:, 2] = float_array[:, 2] * np.sin(float_array[:, 0])
    data_out[:, 3] = float_array[:, 3]

    data_out = np.asarray(data_out).reshape(-1)
    #data_out = data_out.tobytes()

    return data_out

def radian_to_degree(float_array):
    float_array[:, 0] = float_array[:, 0] * 180/np.pi
    float_array[:, 1] = float_array[:, 1] * 180/np.pi
    return float_array
