from time import sleep
import RPi.GPIO as GPIO
# from gpiozero import AngularServo

GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT)

p = GPIO.PWM(2, 50)
p.start(2.5)

try:
    while True:
        p.ChangeDutyCycle(5)
        sleep(0.5)
        p.ChangeDutyCycle(7.5)
        sleep(0.5)
        p.ChangeDutyCycle(10)
        sleep(0.5)
        p.ChangeDutyCycle(12.5)
        sleep(0.5)
        p.ChangeDutyCycle(10)
        sleep(0.5)
        p.ChangeDutyCycle(7.5)
        sleep(0.5)
        p.ChangeDutyCycle(5)
        sleep(0.5)
        p.ChangeDutyCycle(2.5)
        sleep(0.5)
except KeyboardInterrupt:
    p.stop()
    GPIO.cleanup()
