import sys
import paho.mqtt.client as mqtt
import time
import json
from huskylib import HuskyLensLibrary

clientName = "Huskylens"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topic_publish = "pss/movement/auto"
topic_hl = "pss/huskylens"
topic_feedback = "pss/feedback"


def on_connect(client, userdata, flags, rc):
    print("Huskylens connected!")
    mqttClient.publish(topic_feedback, "hl_connected", qos=1)


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic
    pass


def on_publish(client, userdata, result):
    # print("Huskylens published \n")
    pass


mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish
mqttClient.on_message = message_decoder
mqttClient.will_set(topic_feedback, "hl_disconnected", qos=1, retain=False)
mqttClient.username_pw_set("pi", "pissi-pissi")
mqttClient.connect(serverAddress, 1883)
mqttClient.loop_start()

motorSpeed = 50
leftOffset = 80
rightOffset = 240
optWidthLow = 40
optWidthHigh = 80
div = 70
prev_target = None


class Visible:
    prev_state = False  # false for not visible
    first_time = True


'''class Sleep:
    sleep = False'''

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
        mqttClient.publish(topic_feedback, "hl_disconnected")
        sys.exit(1)


def try_connection(timeout):
    for sec in range(timeout):
        if hl.knock() == "Knock Recieved":
            return True

        time.sleep(1)

    return False


def calculate_div(difference):
    if 0 < difference <= 10:
        return 70
    elif 0 < difference <= 15:
        return 100
    elif 0 < difference <= 20:
        return 120

    return 150


def tracking():
    global prev_target
    global div
    hl.algorthim("ALGORITHM_OBJECT_TRACKING")
    Visible.first_time = True
    counter = 0
    while hl.knock() == "Knock Recieved":

        # Check for read response error
        if hl.learnedBlocks() is not None:
            target = hl.getObjectByID(1)
            if target is None:
                continue
            if counter == 0:
                prev_target = target

            if Visible.prev_state is False or Visible.first_time is True:
                Visible.first_time = False
                Visible.prev_state = True
                print("Object visible")
                mqttClient.publish(topic_feedback, "object_visible")

            if target.width < optWidthLow:
                diff = optWidthLow - target.width
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "forward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                print("Huskylens published: forward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            elif target.width > optWidthHigh:
                diff = target.width - optWidthHigh
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "backward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                print("Huskylens published: backward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            if (target.x - (target.width / 2)) < leftOffset:
                diff = leftOffset - (target.x - (target.width / 2))
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "left,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                print("Huskylens published: left,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            elif (target.x + (target.width / 2)) > rightOffset:
                diff = (target.x + (target.width / 2)) - rightOffset
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "right,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                print("Huskylens published: right,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            prev_target = target
            counter = counter + 1

        else:
            if Visible.prev_state is True or Visible.first_time is True:
                Visible.first_time = False
                Visible.prev_state = False
                print("Object lost")
                mqttClient.publish(topic_feedback, "object_lost")

            time.sleep(1)

    print("Connection error occurred")
    mqttClient.publish(topic_feedback, "hl_disconnected")
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
                    mqttClient.publish(topic_feedback, "hl_disconnected")
                    sys.exit(1)
        else:
            print("Failed to connect with huskylens, check hardware")
            mqttClient.publish(topic_feedback, "hl_disconnected")
            sys.exit(1)
    except KeyboardInterrupt:
        print("Terminating program...")
        print('Interrupted by keyboard.')
        sys.exit(0)
