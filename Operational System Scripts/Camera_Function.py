from picamera2 import Picamera2, Preview
from picamera2.controls import Controls
from libcamera import Transform
import RPi.GPIO as GPIO
import tifffile
import matplotlib.pyplot as plt
import time
import numpy as np
from datetime import datetime
import os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set LED Pin
led = 23
GPIO.setup(led, GPIO.OUT)
white_led = 25
GPIO.setup(25,GPIO.OUT)

# Intialize Camera for preview and RGB image
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(
    main={"size": (4056, 3040)},
    lores={"size": (640, 480)},
    display="lores",
    transform=Transform(hflip=1, vflip=1),
)
picam2.configure(camera_config)


# Preview
def start_preview():
    picam2.start_preview(Preview.QTGL)
    picam2.start()


def stop_preview():
    picam2.stop_preview()
    picam2.stop()


# Capture single JPEG image
def capture_jpeg():
    picam2.start()
    time.sleep(3)
    image = picam2.capture_image()
    picam2.stop()
    plt.imshow(image)
    print("Image Ready")
    plt.show()
    

# Capture single RAW image
def capture_raw(LED, exposure, iso):
    global raw
    # Set camera controls
    controls = {"ExposureTime": exposure, #microseconds
            "AnalogueGain": iso, # 1 = ISO 100
            "AeEnable": False, # Auto exposure and Gain
            "AwbEnable": False,# Auto white Balance
            "FrameDurationLimits": (114,239000000)} #Min/Max frame duration
    # Setup config parameters
    preview_config = picam2.create_preview_configuration(raw={"size": picam2.sensor_resolution, "format": "SBGGR12",},
                                                     controls = controls) 
    picam2.configure(preview_config)
    if LED == True:
        GPIO.output(led, GPIO.HIGH) 
        picam2.start() 
        time.sleep(2)
        #Capture image in unpacked RAW format 12bit dynamic range (16bit array)
        raw = picam2.capture_array("raw").view(dtype="uint16")
        GPIO.output(led, GPIO.LOW) 
        print(picam2.capture_metadata())
        picam2.stop()
        plt.imshow(raw, cmap="gray")
        print("RAW Ready")
        plt.show()
    else:
        picam2.start() 
        time.sleep(2)
        #Capture image in unpacked RAW format 12bit dynamic range (16bit array)
        raw = picam2.capture_array("raw").view(dtype="uint16")
        print(picam2.capture_metadata())
        picam2.stop()
        raw_image = plt.imshow(raw, cmap="gray")
        print("RAW Ready")
        plt.show()
        #Clean the figure display
        plt.clf()
    
    #Display Histogram and pixel information of previous image

def display_histogram():
    #Get color channels in bayer order (BGGR)
    red = raw[1::2,1::2]
    green1 = raw[0::2,1::2]
    green2 = raw[1::2,0::2]
    green = np.add(green1,green2)/2
    blue = raw[0::2,0::2]
    #Make histogram for red and green channel # Set camera controls to have good pixel saturation
    Colors=("red","green","blue")
    Channel_ids=(red,green,blue)
    #Calculate the minimum and maximum value of the dataset
    min_value_red = np.min(red)
    min_value_green = np.min(green)
    min_value_blue = np.min(blue)
    max_value_red = np.max(red)
    max_value_green = np.max(green) 
    max_value_blue = np.max(blue)
    min_value = min(min_value_red, min_value_green, min_value_blue)
    max_value = max(max_value_red, max_value_green, max_value_blue)
    for channel_id, c in zip(Channel_ids,Colors):
        histogram, bin_edges=np.histogram(channel_id,bins=4095, range=(min_value,max_value))
        plt.plot(bin_edges[0:-1], histogram, color=c, linewidth = 1)
    plt.title("Red_Green histogram")
    plt.xlabel("Pixel intensity")
    plt.ylabel("Pixel Frequency")
    plt.show()
    
    #Get mean of pixel intensities for each channel
    mean_red = np.mean(red)
    mean_green = np.mean(green)
    mean_blue = np.mean(blue)
    print("Mean value of red:", mean_red)
    print("Mean value of green:", mean_green)
    print("Mean value of blue:", mean_blue)
    #Get MAX pixel intensity for eavh channel
    print("Max value of red:", max_value_red)
    print("Max value of green:", max_value_green)
    print("Max value of blue", max_value_blue)
    # Count number of red and green pixels
    num_red_pixels = np.count_nonzero(red)
    num_green_pixels = np.count_nonzero(green)
    num_blue_pixels =np.count_nonzero(blue)
    print("Number of red pixels:", num_red_pixels)
    print("Number of green pixels:", num_green_pixels)
    print("Number of blue pixels:", num_blue_pixels)
        
#Capture multiple images for calibration
def capture_calibration(o2, num_images, exposure, iso, LED, delay):
    global raw_crop
    # Set camera controls
    controls = {"ExposureTime": exposure, #microseconds
            "AnalogueGain": iso, # 1 = ISO 100
            "AeEnable": False, # Auto exposure and Gain
            "AwbEnable": False,# Auto white Balance
            "FrameDurationLimits": (114,239000000)} #Min/Max frame duration
    # Setup config parameters
    preview_config = picam2.create_preview_configuration(raw={"size": picam2.sensor_resolution, "format": "SBGGR12",},
                                                     controls = controls)
    picam2.configure(preview_config)
    
    if LED == True:
        for i in range(num_images):
            GPIO.output(led, GPIO.HIGH) # Turn on LED

            picam2.start() # Start Camera
            time.sleep(2)

            #Capture image in unpacked RAW format 12bit dynamic range (16bit array)
            raw = picam2.capture_array("raw").view(np.uint16)

            GPIO.output(led, GPIO.LOW) # Turn off LED

            print(picam2.capture_metadata())

            picam2.stop_preview()
            picam2.stop()

            raw_crop = raw[0:3040, 0:4056] # Remove padding from each row of pixels

            base_filename = "RAW"
            save_dir = '/home/martin/Desktop/Calibration_Images/'

            # Create a new folder with date stamp if it does not exist
            date_str = datetime.now().strftime("%Y-%m-%d")
            save_dir = os.path.join(save_dir, f'{base_filename}_{date_str}')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Construct the filename with the user-defined suffix
            #filename = f'{base_filename}_{date_str}_air_sat_{suffix}.tiff'

         # Check if the filename with the user-defined suffix already exists in the folder
            count = 1
            filename = f'{base_filename}_{date_str}_{count}_air_sat{o2}.tiff'
            while os.path.exists(os.path.join(save_dir, filename)):
            # If the filename exists, add a number to the suffix and try again
                filename = f'{base_filename}_{date_str}_{count}_air_sat{o2}.tiff'
                count += 1
            # Save the image with the updated filename
            tifffile.imwrite(os.path.join(save_dir, filename), raw_crop)

            time.sleep(delay)


def capture_measurements(LED, exposure, iso, seq_num):
    global raw
    # Set camera controls
    controls = {"ExposureTime": exposure, #microseconds
            "AnalogueGain": iso, # 1 = ISO 100
            "AeEnable": False, # Auto exposure and Gain
            "AwbEnable": False,# Auto white Balance
            "FrameDurationLimits": (114,239000000)} #Min/Max frame duration
    # Setup config parameters
    preview_config = picam2.create_preview_configuration(raw={"size": picam2.sensor_resolution, "format": "SBGGR12",},
                                                     controls = controls, transform=Transform(hflip=1, vflip=1)) 
    picam2.configure(preview_config)
    if LED == True:
        GPIO.output(led, GPIO.HIGH) 
        picam2.start() 
        time.sleep(2)
        #Capture image in unpacked RAW format 12bit dynamic range (16bit array)
        raw = picam2.capture_array("raw").view(dtype="uint16")
        GPIO.output(led, GPIO.LOW) 
        print(picam2.capture_metadata())
        picam2.stop()
        raw_crop = raw[0:3040, 0:4056] # Remove padding from each row of pixels

        base_filename = "RAW"
        save_dir = '/home/martin/Desktop/Measurement_Images/'
        # Create a new folder with date stamp if it does not exist
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_dir = os.path.join(save_dir, f'{base_filename}_{date_str}')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        # Check if the filename with the user-defined suffix already exists in the folder
        count = 1
        filename = f'{base_filename}_{date_str}_{count}_seq_num{seq_num}.tiff'
        while os.path.exists(os.path.join(save_dir, filename)):
            # If the filename exists, add a number to the suffix and try again
            filename = f'{base_filename}_{date_str}_{count}_seq_num{seq_num}.tiff'
            count += 1
            # Save the image with the updated filename
        tifffile.imwrite(os.path.join(save_dir, filename), raw_crop) 
              
   
            














    
    
    
    
 