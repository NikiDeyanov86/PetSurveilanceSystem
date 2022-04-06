import time

import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)
GPIO.setup(11, GPIO.OUT)
GPIO.output(11, GPIO.LOW)

time.sleep(0.25)

GPIO.output(17, GPIO.HIGH)
GPIO.cleanup()