import sys
import paho.mqtt.client as mqtt
import time
import json
from clients.huskylib import HuskyLensLibrary
from clients.motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb

left = MotorSide(ena, in1, in2)
right = MotorSide(enb, in3, in4)
motors = MotorDriver(left, right)

try:
    hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB0", 115200)
except:
    try:
        hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB1", 115200)
    except:
        print("Cannot create serial communication, check your hardware connections!")
        sys.exit(1)

hl.algorthim("ALGORITHM_OBJECT_TRACKING")

motors.stop()
motors.move_forward_hl(0.2, 50)

while hl.knock() == "Knock Recieved":

    if hl.learnedBlocks() is not None:
        target = hl.getObjectByID(1)
        print("COORDINATES - ({x}, {y}) / WIDTH: {w}".format(x=target.x, y=target.y, w=target.width))
        time.sleep(3)

