from time import sleep
# import RPi.GPIO as GPIO
from gpiozero import AngularServo

servo1 = AngularServo(2, min_angle=0, max_angle=180,
                      min_pulse_width=0.0005,
                      max_pulse_width=0.0024)

servo1.angle = 0
sleep(2)
servo1.angle = 90
sleep(2)
servo1.angle = 180

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(18, GPIO.OUT)

