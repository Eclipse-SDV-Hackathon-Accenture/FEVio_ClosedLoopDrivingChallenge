# ========================= eCAL LICENSE =================================
#
# Copyright (C) 2016 - 2019 Continental Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ========================= eCAL LICENSE =================================

import argparse
import os
import sys
import time

import ecal.core.core as ecal_core
from ecal.core.subscriber import ProtoSubscriber
from ecal.core.publisher  import ProtoPublisher

from ros.sensor_msgs.Image_pb2 import Image as ROSImage
from ros.sensor_msgs.CompressedImage_pb2 import CompressedImage as ROSCompressedImage
from ros.visualization_msgs.ImageMarker_pb2 import ImageMarker as ROSImageMarker
from ros.visualization_msgs.ImageMarkerArray_pb2 import ImageMarkerArray as ROSImageMarkerArray
from ros.geometry_msgs.Point_pb2 import Point as ROSPoint
from ros.std_msgs.Time_pb2 import Time
from ros.std_msgs.ColorRGBA_pb2 import ColorRGBA

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from PIL import Image
import io

import numpy as np

def mediapip_image_from_ros_raw_image(image: ROSImage) -> mp.Image:
  # create numpy array with imagedata in uint8 to make it usable for mediapipe
  np_array = np.frombuffer(image.data, dtype=np.uint8)
  np_array = np.reshape(np_array, newshape=(image.height, image.width, 3))

  # mediapipe image created out of numpy array data
  mp_image = mp.Image(
   image_format=mp.ImageFormat.SRGB, data=np_array
  )
  return mp_image

def create_bounding_box(detection, header) -> ROSImageMarker:
  bbox = detection.bounding_box
  bounding_box = ROSImageMarker()
  bounding_box.type = 3 #Polygon
  lower_left = ROSPoint(x=bbox.origin_x, y=bbox.origin_y)
  lower_right = ROSPoint(x=bbox.origin_x + bbox.width, y=bbox.origin_y)
  upper_right = ROSPoint(x=bbox.origin_x + bbox.width, y=bbox.origin_y + bbox.height)
  upper_left = ROSPoint(x=bbox.origin_x, y=bbox.origin_y + bbox.height)
  bounding_box.points.append(lower_left)
  bounding_box.points.append(lower_right)
  bounding_box.points.append(upper_right)
  bounding_box.points.append(upper_left)
  bounding_box.scale = 4
  bounding_box.header.stamp.sec = header.stamp.sec
  bounding_box.header.stamp.nsec = header.stamp.nsec
  bounding_box.outline_color.r = 1.0
  bounding_box.outline_color.g = 0.647
  bounding_box.outline_color.b = 0.0
  bounding_box.outline_color.a = 1.0
  return bounding_box

def create_annotations(detection_result, timestamp) -> ROSImageMarkerArray:
  annotations = ROSImageMarkerArray()
  for detection in detection_result.detections:
    if (detection.categories[0].category_name == "car"):
      bounding_box = create_bounding_box(detection, timestamp)
      annotations.markers.append(bounding_box)
  return annotations

class ImageClassifier(object):
  
  def __init__(self):
    BaseOptions = mp.tasks.BaseOptions
    ObjectDetector = mp.tasks.vision.ObjectDetector
    ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    model_path = os.path.join(os.path.dirname(__file__), 'efficientdet_lite0.tflite')

    self.options = ObjectDetectorOptions(
      base_options=BaseOptions(model_asset_path=model_path),
      running_mode=VisionRunningMode.VIDEO,
      max_results=15
    )
    self.detector = ObjectDetector.create_from_options(self.options)

  def reset(self):
    ObjectDetector = mp.tasks.vision.ObjectDetector
    self.detector = ObjectDetector.create_from_options(self.options)

def main():
  args = parse_arguments()
  
  # print eCAL version and date
  print("eCAL {} ({})\n".format(ecal_core.getversion(),ecal_core.getdate()))
  
  # initialize eCAL API
  ecal_core.initialize(sys.argv, "annotate images")
  
  # set process state
  ecal_core.set_process_state(1, 1, "I feel good")

  # create subscriber and connect callback
  sub = ProtoSubscriber(args.input, ROSImage)
  pub = ProtoPublisher(args.output, ROSImageMarkerArray)
  
  classifier = ImageClassifier()
  last_time = 0

  while ecal_core.ok():
    ret, image, time = sub.receive(500)

    if ret > 0:
      if time < last_time:
        classifier.reset()

      last_time = time
      
      mp_image = mediapip_image_from_ros_raw_image(image)
      #print(mp_image)
      detection_result = classifier.detector.detect_for_video(mp_image, time)
      for detection in detection_result.detections:
        if (detection.categories[0].category_name == "car"):
          print(detection)

      annotations = create_annotations(detection_result, image.header)
      pub.send(annotations)

  ecal_core.finalize()
  
def parse_arguments():
  parser = argparse.ArgumentParser(description="Application to detect vehicles in an Image")
  parser.add_argument("--input",  default="camera/cam_front_left")
  parser.add_argument('--output', default="annotations/cam_front_left")
  args = parser.parse_args()     
  return args
 
if __name__ == "__main__":
  main()  
