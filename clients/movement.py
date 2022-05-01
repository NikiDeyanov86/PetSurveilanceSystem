import paho.mqtt.client as mqtt
from motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb, power, \
                        servo_horizontal, ServoTask
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
from queue import Queue

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


class Check:
    manual = True
    obstacle = False
    current_process = None
    servo_task = None


def check_for_obstacle():
    print("Asking is it free?")
    mqttClient.publish(topic_feedback, "free?", qos=1)


def connect(client, userdata, flags, rc):
    mqttClient.subscribe(topics)
    mqttClient.subscribe(topic_feedback)
    print("Connected! Subscribed to <pss/movement/+> and <pss/feedback>")
    mqttClient.publish(topic_feedback, "mov_connected", qos=1)


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic
    queue.put(msg)
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
        speed = 50
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

        if message == "left":
            Check.servo_task = ServoTask()
            Check.servo_task.positive(servo_horizontal)
            print("Creating left process")

        elif message == "right":
            Check.servo_task = ServoTask()
            Check.servo_task.negative(servo_horizontal)
            print("Creating right process")

        elif message == "stop":
            print("Stop received")
            Check.servo_task.terminate()

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


scheduler = BackgroundScheduler()
queue = Queue()
scheduler.add_job(check_for_obstacle, 'interval', seconds=5)
mqttClient.on_connect = connect
mqttClient.on_message = message_decoder
mqttClient.will_set(topic_feedback, "mov_disconnected", qos=1, retain=False)
mqttClient.username_pw_set("pi", "pissi-pissi")
mqttClient.connect(serverAddress, 1883)


def check_for_messages_in_queue():
    while True:
        if not queue.empty():

            next_message = queue.get()
            if next_message is None:
                continue

            if next_message.topic == topic_camera_movement:
                payload = next_message.payload.decode(encoding='UTF-8')

                if payload == "left":
                    print("Creating left process")
                    Check.servo_task = ServoTask()
                    Check.current_process = Thread(target=Check.servo_task.positive(servo_horizontal))
                    Check.current_process.start()

                elif payload == "right":
                    print("Creating right process")
                    Check.servo_task = ServoTask()
                    Check.current_process = Thread(target=Check.servo_task.negative(servo_horizontal))
                    Check.current_process.start()

                elif payload == "stop":
                    print("Stop received")
                    Check.servo_task.terminate()


if __name__ == '__main__':
    mqttClient.loop_start()
    check_for_messages_in_queue_task = Thread(target=check_for_messages_in_queue())
    check_for_messages_in_queue_task.start()
    check_for_messages_in_queue_task.join()
