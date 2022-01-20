import sys
import paho.mqtt.client as mqtt
import time
import json
from huskylib import HuskyLensLibrary

clientName = "Huskylens"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topic_publish = "pss/movement/auto"
topic_subscribe = "pss/huskylens"
topic_feedback = "pss/feedback"


def on_connect(client, userdata, flags, rc):
    print("Huskylens connected!")


def on_publish(client, userdata, result):
    # print("Huskylens published \n")
    pass


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    # decode the message from the server
    pass


mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish
mqttClient.on_subscribe = message_decoder
mqttClient.will_set(topic_publish, "disconnected", qos=1, retain=False)
mqttClient.connect(serverAddress, 1883)
mqttClient.loop_start()

motorSpeed = 80
leftOffset = 125
rightOffset = 185
topOffset = 80
bottomOffset = 160
optWidthLow = 50
optWidthHigh = 80
prev_target = None

hl = None

# make an if that catches exception if serial connection
# failes and tries to connect on USB1
try:
    hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB0", 115200)
except:
    try:
        hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB1", 115200)
    except:
        print("Cannot create serial communication, check your hardware connections!")
        mqttClient.publish(topic_publish, "disconnected")
        sys.exit(1)


def try_connection(timeout):
    for sec in range(timeout):
        if hl.knock() == "Knock Recieved":
            return True

        time.sleep(1)

    return False


def tracking():
    hl.algorthim("ALGORITHM_OBJECT_TRACKING")

    counter = 0
    while hl.knock() == "Knock Recieved":

        # Check for read response error 
        if hl.learnedBlocks() is not None:
            mqttClient.publish(topic_feedback, "object_visible")
            target = hl.getObjectByID(1)
            if target is None:
                continue
            if counter == 0:
                prev_target = target

            if target.width < optWidthLow:
                diff = optWidthLow - target.width
                mqttClient.publish(topic_publish, "forward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                print("Huskylens published: forward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                time.sleep(diff / 25)

            elif target.width > optWidthHigh:
                diff = target.width - optWidthHigh
                mqttClient.publish(topic_publish, "backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                print("Huskylens published: backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                time.sleep(diff / 25)

            if target.x < leftOffset:
                diff = leftOffset - target.x
                mqttClient.publish(topic_publish, "left,{sec},{speed}".format(sec=diff / 20, speed=100))
                print("Huskylens published: left,{sec},{speed}".format(sec=diff / 20, speed=100))
                time.sleep(diff / 20)

            elif target.x > rightOffset:
                diff = target.x - rightOffset
                mqttClient.publish(topic_publish, "right,{sec},{speed}".format(sec=diff / 20, speed=100))
                print("Huskylens published: right,{sec},{speed}".format(sec=diff / 20, speed=100))
                time.sleep(diff / 20)

            if target.y < topOffset:
                if target.width < prev_target.width:
                    diff = topOffset - target.y
                    mqttClient.publish(topic_publish, "forward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                    print("Huskylens published: forward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                    time.sleep(diff / 25)

                elif target.width > prev_target.width:
                    diff = topOffset - target.y
                    mqttClient.publish(topic_publish, "backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                    print("Huskylens published: backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                    time.sleep(diff / 25)

            elif target.y > bottomOffset:
                diff = target.y - bottomOffset
                mqttClient.publish(topic_publish, "backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                print("Huskylens published: backward,{sec},{speed}".format(sec=diff / 25, speed=motorSpeed))
                time.sleep(diff / 25)

            prev_target = target
            counter = counter + 1

        else:
            print("Object lost")
            mqttClient.publish(topic_publish, "object_lost")
            time.sleep(1)

    print("Connection error occured")
    mqttClient.publish(topic_publish, "disconnected")
    sys.exit(1)


if __name__ == '__main__':
    try:
        if hl is not None:
            if hl.knock() == "Knock Recieved":
                tracking()
            else:
                if try_connection(10) is True:
                    tracking()
                else:
                    print("Failed to connect with huskylens, check hardware")
                    mqttClient.publish(topic_publish, "disconnected")
                    sys.exit(1)
        else:
            print("Failed to connect with huskylens, check hardware")
            mqttClient.publish(topic_publish, "disconnected")
            sys.exit(1)
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
