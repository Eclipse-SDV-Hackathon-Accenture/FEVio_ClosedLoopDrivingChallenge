import ros.sensor_msgs.Image_pb2 as img
import carla

def image_to_msg(rgb_image: carla.Image, frame_id):
        message = img.Image()

        message = set_header(message, rgb_image, frame_id)
        message.height = rgb_image.height
        message.width = rgb_image.width
        message.encoding = "bgra8"
        message.is_bigendian = 0
        message.step = 4 * rgb_image.width
        message.data = bytes(rgb_image.raw_data)

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

def get_msg_type():
    return img.Image