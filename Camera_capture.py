from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (4056,3040)}, lores={"size": (640,480)}, display="lores")
picam2.configure(camera_config)

picam2.start_preview(Preview.QTGL)
picam2.start()
time.sleep(5)
picam2.capture_file('/home/martin/Desktop/test.jpg')

#Hello