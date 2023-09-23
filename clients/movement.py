import paho.mqtt.client as mqtt
from motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb, power, \
    servo_horizontal, servo_vertical
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
from queue import Queue
from time import sleep

left = MotorSide(ena, in1, in2)
right = MotorSide(enb, in3, in4)
motors = MotorDriver(left, right)

clientName = "Movement"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)

topics = "pss/movement/#"
topic_feedback = "pss/feedback"
topic_mov = "pss/movement/proximity"
topic_motors_power = "pss/movement/motors_power"
topic_camera_movement = "pss/movement/camera"
topic_camera_setting = "pss/movement/camera/center"

scheduler = BackgroundScheduler()
camera_queue = Queue()


class Check:
    manual = True
    obstacle = False
    camera_center = None


def check_for_obstacle():
    print("Asking is it free?")
    mqttClient.publish(topic_feedback, "free?", qos=1)


def on_connect(client, userdata, flags, rc):
    mqttClient.subscribe(topics)
    mqttClient.subscribe(topic_feedback)
    print("Connected! Subscribed to <pss/movement/+> and <pss/feedback>")
    mqttClient.publish(topic_feedback, "mov_connected", qos=1)


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic

    # Synchronize auto and manual

    if topic == "pss/movement/auto" and Check.manual is False:
        # Data from Huskylens, ex. "<direction>,<seconds>,<speed>"
        split = message.split(",")
        direction = split[0]
        seconds = float(split[1])
        speed = int(split[2])

        if direction == "forward":
            print("AUTO: Forward")
            motors.move_forward_hl(seconds, speed)

        elif direction == "backward":
            print("AUTO: Backward")
            motors.move_backward_hl(seconds, speed)

        elif direction == "left":
            print("AUTO: Left")
            motors.turn_left_hl(seconds, speed)

        elif direction == "right":
            print("AUTO: Right")
            motors.turn_right_hl(seconds, speed)

    elif topic == "pss/movement/manual" and Check.manual is True:
        # Data from remote client, ex. "left" ---- time ----> "stop"
        direction = message
        speed = 65
        if Check.camera_center is True:
            servo_horizontal.angle = 0  # center the camera
            servo_vertical.angle = 0

        if direction == "forward":
            if Check.obstacle is False:
                print("MANUAL: forward")
                motors.forward(speed)
            pass

        elif direction == "backward":
            print("MANUAL: backward")
            motors.backward(speed)
            pass
        elif direction == "left":
            print("MANUAL: left")
            motors.left(speed + 5)
            pass
        elif direction == "right":
            print("MANUAL: right")
            motors.right(speed + 5)
            pass
        elif direction == "stop":
            print("MANUAL: stop")
            motors.stop()
            pass

    elif topic == "pss/movement/mode":
        if message == "auto":
            print("<<<<<<<< AUTO MODE >>>>>>>>>")
            Check.manual = False
        elif message == "manual":
            print("<<<<<<<< MANUAL MODE >>>>>>>>>")
            Check.manual = True

    elif topic == topic_motors_power:
        if message == "on":
            power(1)

        elif message == "off":
            power(0)

    elif topic == topic_mov:
        if message == "obstacle":
            motors.stop()
            Check.obstacle = True
            print("OBSTACLE!")
            if scheduler.running is False:
                scheduler.start()
            else:
                scheduler.resume()
        elif message == "free":
            Check.obstacle = False
            print("FREE TO MOVE!")
            scheduler.pause()

    elif topic == topic_camera_movement:
        camera_queue.put(message)

    elif topic == topic_camera_setting:
        if message == "check":
            Check.camera_center = True
        elif message == "uncheck":
            Check.camera_center = False

    elif topic == topic_feedback:
        if message == "hl_connected":
            print("Huskylens connected")

        elif message == "hl_disconnected":
            print("Huskylens disconnected")

        if message == "us_connected":
            print("Ultrasonic connected")

        elif message == "us_disconnected":
            print("Ultrasonic disconnected")
            Check.obstacle = False


def check_for_messages_in_camera_queue():
    flag = 0  # 0 - no movement; 1 - left; 2 - right; 3 - up; 4 - down
    while True:
        if not camera_queue.empty():
            next_message = camera_queue.get()
            if next_message is None:
                continue

            if next_message == "left":
                flag = 1

            elif next_message == "right":
                flag = 2

            elif next_message == "up":
                flag = 3

            elif next_message == "down":
                flag = 4

            elif next_message == "stop":
                flag = 0

        if flag == 0:
            continue

        elif flag == 1:
            if servo_horizontal.angle <= 80:
                servo_horizontal.angle += 10
                sleep(0.1)
            else:
                servo_horizontal.angle = 90
                continue

        elif flag == 2:
            if servo_horizontal.angle >= -80:
                servo_horizontal.angle -= 10
                sleep(0.1)
            else:
                servo_horizontal.angle = -90
                continue

        elif flag == 3:
            if servo_vertical.angle <= 80:
                servo_vertical.angle += 10
                sleep(0.1)
            else:
                servo_vertical.angle = 90
                continue

        elif flag == 4:
            if servo_vertical.angle >= -80:
                servo_vertical.angle -= 10
                sleep(0.1)
            else:
                servo_vertical.angle = -90
                continue


def init_mqtt_client(client: mqtt.Client):
    client.on_connect = on_connect
    client.on_message = message_decoder
    client.will_set(topic_feedback, "mov_disconnected",
                    qos=1, retain=False)
    client.username_pw_set("pi", "pissi-pissi")
    client.connect(serverAddress, 1883)
    client.loop_start()


if __name__ == '__main__':
    init_mqtt_client(mqttClient)
    camera_task = Thread(target=check_for_messages_in_camera_queue)
    camera_task.start()
    camera_task.join()
