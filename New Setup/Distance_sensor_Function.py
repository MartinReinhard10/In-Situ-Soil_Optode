import busio
import board
from adafruit_vl53l0x import VL53L0X

# Set up the I2C and VL53L0X sensor
i2c = busio.I2C(board.SCL, board.SDA)
tof = VL53L0X(i2c)

distance_values = []

def measure_distance(label):
    # Perform distance measurement and return the distance in mm
    distance_mm = tof.range

    # Append the distance to the list
    distance_values.append(distance_mm)

    # Check if we have collected 5 distance values
    if len(distance_values) == 5:
        # Calculate the mean of the collected distance values
        mean_distance = sum(distance_values) / len(distance_values)
        
        # Clear the list for the next 5 measurements
        distance_values.clear()
        
        # Update the label with the mean distance value
        label.config(text="Mean distance from bottom: {} mm".format(mean_distance))

    # Schedule the next measurement after 1 second
    label.after(1000, measure_distance, label)


