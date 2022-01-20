import paho.mqtt.client as mqtt
from motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb

left = MotorSide(ena, in1, in2)
right = MotorSide(enb, in3, in4)
motors = MotorDriver(left, right)

clientName = "Movement"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topics = "pss/movement/+"
topic_feedback = "pss/feedback"


class Check:
    manual = True


def connect(client, userdata, flags, rc):
    print("subscribing")
    mqttClient.subscribe(topics)
    print("subscribed to <pss/movement/+>")


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic
    # Syncronize auto and manual

    if topic == "pss/movement/auto" and Check.manual is False:
        # Data from Huskylens, ex. "<direction>,<seconds>,<speed>"
        if message == "disconnected":
            print("Connection with huskylens ended")
            # huskylens is down
            # switch to manual mode
            mqttClient.publish(topic_feedback, "huskylens_disconnected")
            pass

        elif message == "object_lost":
            print("Object lost")
            # object is lost
            # switch to manual mode
            mqttClient.publish(topic_feedback, "object_lost")
            pass

        else:
            split = message.split(",")
            direction = split[0]
            seconds = float(split[1])
            speed = int(split[2])

            if direction == "forward":
                print("AUTO: Forward")
                motors.move_forward_hl(seconds, speed)
                motors.stop()

            elif direction == "backward":
                print("AUTO: Backward")
                motors.move_backward_hl(seconds, speed)
                motors.stop()

            elif direction == "left":
                print("AUTO: Left")
                motors.turn_left_hl(seconds, speed)
                motors.stop()

            elif direction == "right":
                print("AUTO: Right")
                motors.turn_right_hl(seconds, speed)
                motors.stop()

    elif topic == "pss/movement/manual" and Check.manual is True:
        # Data from remote client, ex. "left" ---- time ----> "stop"
        direction = message
        speed = 100
        if direction == "forward":
            print("MANUAL: forward")
            motors.forward(speed)
            pass
        elif direction == "backward":
            print("MANUAL: forward")
            motors.backward(speed)
            pass
        elif direction == "left":
            print("MANUAL: forward")
            motors.left(speed)
            pass
        elif direction == "right":
            print("MANUAL: forward")
            motors.right(speed)
            pass
        elif direction == "stop":
            print("MANUAL: forward")
            motors.stop()
            pass

    elif topic == "pss/movement/mode":
        if message == "auto":
            Check.manual = False
        elif message == "manual":
            Check.manual = True


mqttClient.on_connect = connect
mqttClient.on_message = message_decoder

# Connect to the MQTT server & loop forever.
# CTRL-C will stop the program from running.
mqttClient.connect(serverAddress)
mqttClient.loop_start()
