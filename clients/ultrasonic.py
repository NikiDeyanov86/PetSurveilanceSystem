import RPi.GPIO as GPIO
import time
import sys
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BOARD)

TRIG = 12
ECHO = 37
stopped = False

clientName = "Ultrasonic"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topic_mov = "pss/movement/proximity"
topic_feedback = "pss/feedback"


def on_connect(client, userdata, flags, rc):
    print("Ultrasonic connected!")
    mqttClient.publish(topic_feedback, "us_connected", qos=1)


def on_publish(client, userdata, result):
    print("Published.")


mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish
mqttClient.will_set(topic_feedback, "us_disconnected", qos=1, retain=False)
mqttClient.connect(serverAddress, 1883)


def measure():
    global stopped
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

    GPIO.output(TRIG, False)
    print("Calibrating.....")
    time.sleep(2)

    while True:
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 17150

        distance = round(distance + 1.15, 2)
        print("Distance is: ", distance, "cm.")

        if distance <= 10 and stopped is False:
            mqttClient.publish(topic_mov, "obstacle")
            print("Obstacle")
            stopped = True

        elif distance > 10 and stopped is True:
            mqttClient.publish(topic_mov, "free")
            print("Free")
            stopped = False


if __name__ == '__main__':
    mqttClient.loop_start()
    try:
        measure()
    except KeyboardInterrupt:
        GPIO.cleanup()