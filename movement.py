import paho.mqtt.client as mqtt
from motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb

left = MotorSide(ena, in1, in2)
right = MotorSide(enb, in3, in4)
motors = MotorDriver(left, right)

clientName = "Movement"
serverAddress = "localhost"
mqttClient = mqtt.Client(clientName)
topics = "pss/movement/+"


def connect(client, userdata, flags, rc):
    print("subscribing")
    mqttClient.subscribe(topics)
    print("subscribed to <pss/movement/+>")


def message_decoder(client, userdata, msg):
    message = msg.payload.decode(encoding='UTF-8')
    topic = msg.topic
    # Syncronize auto and manual

    if topic == "pss/movement/auto":
        # Data from Huskylens, ex. "<direction>,<seconds>,<speed>"
        if message == "disconnected":
            print("Connection with huskylens ended")
            # huskylens is down
            # switch to manual mode
            pass

        elif message == "object_lost":
            print("Object lost")
            # object is lost
            # switch to manual mode
            pass

        else:
            split = message.split(",")
            direction = split[0]
            seconds = float(split[1])
            speed = int(split[2])

            if direction == "forward":
                print("Forward")
                motors.move_forward_hl(seconds, speed)
                motors.stop()

            elif direction == "backward":
                print("Backward")
                motors.move_backward_hl(seconds, speed)
                motors.stop()

            elif direction == "left":
                print("Left")
                motors.turn_left_hl(seconds, speed)
                motors.stop()

            elif direction == "right":
                print("Right")
                motors.turn_right_hl(seconds, speed)
                motors.stop()

    elif topic == "pss/movement/manual":
        # Data from remote client, ex. "left" ---- time ----> "stop"
        direction = message
        speed = 100
        if direction == "forward":
            motors.forward(speed)
            pass
        elif direction == "backward":
            motors.backward(speed)
            pass
        elif direction == "left":
            motors.left(speed)
            pass
        elif direction == "right":
            motors.right(speed)
            pass
        elif direction == "stop":
            motors.stop()
            pass


mqttClient.on_connect = connect
mqttClient.on_message = message_decoder

# Connect to the MQTT server & loop forever.
# CTRL-C will stop the program from running.
mqttClient.connect(serverAddress)
mqttClient.loop_forever()
