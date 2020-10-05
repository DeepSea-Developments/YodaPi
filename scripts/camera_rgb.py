from io import BytesIO

try:
    import picamera

    rgb_cam = picamera.PiCamera()
    rgb_cam.rotation = 180
    rgb_cam.hflip = True
    rgb_cam.resolution = (640, 480)
except:
    print("ModuleNotFoundError: No module named 'picamera'")


def capture(img_format='jpeg', img_quality=85):
    image_stream = BytesIO()
    rgb_cam.capture(image_stream, img_format, img_quality)
    image_rgb = image_stream.getvalue()
    return image_rgb
