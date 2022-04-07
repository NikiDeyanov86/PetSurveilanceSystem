import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
print("Pin set")

print("Setting to low")
GPIO.output(18, False)
print("Set to low")

time.sleep(5)

print("Setting to HIGH")
GPIO.output(18, True)
print("Set to high")
time.sleep(2)
GPIO.cleanup()
