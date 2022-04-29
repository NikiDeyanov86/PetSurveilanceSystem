from gpiozero import Servo, AngularServo
from time import sleep
import RPi.GPIO as GPIO

p = GPIO.PWM(2, 50)
servo = AngularServo(p, min_angle=-90, max_angle=90)

try:
    while True:
        servo.angle = 0
        sleep(2)
        servo.angle = -90
        sleep(2)
        servo.angle = 90
        sleep(2)

except KeyboardInterrupt:
    print("Program stopped")

