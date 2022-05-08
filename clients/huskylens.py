import sys
import paho.mqtt.client as mqtt
import time
import json
from huskylib import HuskyLensLibrary

clientName = "Huskylens"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topic_publish = "pss/movement/auto"
topic_feedback = "pss/feedback"


def on_connect(client, userdata, flags, rc):
    print("Huskylens connected!")
    mqttClient.publish(topic_feedback, "hl_connected", qos=1)


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic
    pass


mqttClient.on_connect = on_connect
mqttClient.on_message = message_decoder
mqttClient.will_set(topic_feedback, "hl_disconnected", qos=1, retain=False)
mqttClient.username_pw_set("pi", "pissi-pissi")
mqttClient.connect(serverAddress, 1883)


motorSpeed = 40
leftOffset = 80
rightOffset = 240
optWidthLow = 40
optWidthHigh = 80
div = 70


class Visible:
    prev_state = False  # false for not visible
    first_time = True


hl = None

try:
    hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB0", 115200)
except Exception:
    try:
        hl = HuskyLensLibrary("SERIAL", "/dev/ttyUSB1", 115200)
    except Exception:
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
    global div
    hl.algorthim("ALGORITHM_OBJECT_TRACKING")
    Visible.first_time = True

    while hl.knock() == "Knock Recieved":

        if hl.learnedBlocks() is not None:
            target = hl.getObjectByID(1)
            if target is None:
                continue

            if Visible.prev_state is False or Visible.first_time is True:
                Visible.first_time = False
                Visible.prev_state = True
                mqttClient.publish(topic_feedback, "object_visible")

            if target.width < optWidthLow:
                diff = optWidthLow - target.width
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "forward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            elif target.width > optWidthHigh:
                diff = target.width - optWidthHigh
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "backward,{sec},{speed}".format(sec=diff / div, speed=motorSpeed))
                time.sleep(diff / div)

            if (target.x - (target.width / 2)) < leftOffset:
                diff = leftOffset - (target.x - (target.width / 2))
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "left,{sec},{speed}".format(sec=diff / div, speed=motorSpeed+5))
                time.sleep(diff / div)

            elif (target.x + (target.width / 2)) > rightOffset:
                diff = (target.x + (target.width / 2)) - rightOffset
                div = calculate_div(diff)
                mqttClient.publish(topic_publish, "right,{sec},{speed}".format(sec=diff / div, speed=motorSpeed+5))
                time.sleep(diff / div)

        else:
            if Visible.prev_state is True or Visible.first_time is True:
                Visible.first_time = False
                Visible.prev_state = False
                mqttClient.publish(topic_feedback, "object_lost")

            time.sleep(1)

    print("Connection error occurred")
    mqttClient.publish(topic_feedback, "hl_disconnected")
    sys.exit(1)


if __name__ == '__main__':
    mqttClient.loop_start()
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
