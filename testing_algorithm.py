import sys
import paho.mqtt.client as mqtt
import time
import json
from clients.huskylib import HuskyLensLibrary

try:
    hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB0", 115200)
except:
    try:
        hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB1", 115200)
    except:
        print("Cannot create serial communication, check your hardware connections!")
        sys.exit(1)

hl.algorthim("ALGORITHM_OBJECT_TRACKING")

while hl.knock() == "Knock Recieved":

    if hl.learnedBlocks() is not None:
        target = hl.getObjectByID(1)
        print("COORDINATES - ({x}, {y}) / WIDTH: {w}".format(x=target.x, y=target.y, w=target.width))
        time.sleep(3)

