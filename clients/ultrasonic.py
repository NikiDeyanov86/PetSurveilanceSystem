import RPi.GPIO as GPIO
import time
import sys
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BOARD)

TRIG = 38
ECHO = 37


class Check:
    stopped = False


clientName = "Ultrasonic"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topic_mov = "pss/movement/proximity"
topic_feedback = "pss/feedback"


def on_connect(client, userdata, flags, rc):
    print("Ultrasonic connected!")
    mqttClient.subscribe(topic_feedback)
    mqttClient.publish(topic_feedback, "us_connected", qos=1)


def on_publish(client, userdata, result):
    print("Published.")


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic

    if message == "free?":
        measure(check=True)


mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish
mqttClient.on_message = message_decoder
mqttClient.will_set(topic_feedback, "us_disconnected", qos=1, retain=False)
mqttClient.username_pw_set("pi", "pissi-pissi")
mqttClient.connect(serverAddress, 1883)


def measure(check):

    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

    GPIO.output(TRIG, False)
    print("Calibrating.....")
    time.sleep(2)

    while True:
        # print("In loop...")
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            # print("Transiting...")

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            # print("Receiving...")

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 17150

        distance = round(distance + 1.15, 2)
        # print("Distance is: ", distance, "cm.")

        if check is True:
            if distance > 25:
                mqttClient.publish(topic_mov, "free")
                Check.stopped = False

            check = False

        else:
            if distance <= 25 and Check.stopped is False:
                mqttClient.publish(topic_mov, "obstacle")
                print("Obstacle")
                Check.stopped = True

            elif distance > 25 and Check.stopped is True:
                mqttClient.publish(topic_mov, "free")
                print("Free")
                Check.stopped = False

        time.sleep(0.1)


if __name__ == '__main__':
    mqttClient.loop_start()
    try:
        measure(check=False)
    finally:
        GPIO.cleanup()
