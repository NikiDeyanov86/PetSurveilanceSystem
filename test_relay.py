import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
print("Pin set")

time.sleep(5)

print("Setting to HIGH")
GPIO.output(17, GPIO.HIGH)
print("Set to high")
time.sleep(2)
GPIO.cleanup()
