import RPi.GPIO as gpio
import time

in1 = 22
in2 = 23
in3 = 24
in4 = 25
ena = 12
enb = 13

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)


class MotorSide:
    def __init__(self, en, in1, in2):
        self.en = en
        self.in1 = in1
        self.in2 = in2
        gpio.setup(en, gpio.OUT)
        gpio.setup(in1, gpio.OUT)
        gpio.setup(in2, gpio.OUT)
        self.pwm = gpio.PWM(en, 100)
        self.pwm.start(0)

    def forward(self, speed):
        self.pwm.ChangeDutyCycle(speed)
        gpio.output(self.in1, True)
        gpio.output(self.in2, False)

    def reverse(self, speed):
        self.pwm.ChangeDutyCycle(speed)
        gpio.output(self.in1, False)
        gpio.output(self.in2, True)

    def stop(self):
        self.pwm.ChangeDutyCycle(0)
        gpio.output(self.in1, False)
        gpio.output(self.in2, False)


class MotorDriver:
    def __init__(self, left, right):
        self.right_side = right
        self.left_side = left

    def move_forward_hl(self, sec, speed):
        self.left_side.forward(speed)
        self.right_side.forward(speed)
        time.sleep(sec)
        self.stop()

    def move_backward_hl(self, sec, speed):
        self.left_side.reverse(speed)
        self.right_side.reverse(speed)
        time.sleep(sec)
        self.stop()

    def turn_left_hl(self, sec, speed):
        self.left_side.reverse(speed)
        self.right_side.forward(speed)
        time.sleep(sec)
        self.stop()

    def turn_right_hl(self, sec, speed):
        self.left_side.forward(speed)
        self.right_side.reverse(speed)
        time.sleep(sec)
        self.stop()

    def forward(self, speed):
        self.left_side.forward(speed)
        self.right_side.forward(speed)

    def backward(self, speed):
        self.left_side.reverse(speed)
        self.right_side.reverse(speed)

    def left(self, speed):
        self.left_side.reverse(speed)
        self.right_side.forward(speed)

    def right(self, speed):
        self.left_side.forward(speed)
        self.right_side.reverse(speed)

    def stop(self):
        self.left_side.stop()
        self.right_side.stop()

    def tear_down(self):
        gpio.cleanup()
