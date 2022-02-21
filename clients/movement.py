import paho.mqtt.client as mqtt
from motorslib import MotorSide, MotorDriver, in1, in2, in3, in4, ena, enb

try:
    left = MotorSide(ena, in1, in2)
    right = MotorSide(enb, in3, in4)
    motors = MotorDriver(left, right)

    clientName = "Movement"
    serverAddress = "localhost"
    mqttClient = mqtt.Client(clientName)
    topics = "pss/movement/+"
    topic_feedback = "pss/feedback"
    topic_mov = "pss/movement/proximity"


    class Check:
        manual = True
        obstacle = False


    def connect(client, userdata, flags, rc):
        mqttClient.subscribe(topics)
        mqttClient.subscribe(topic_feedback)
        mqttClient.subscribe(topic_mov)
        print("Connected! Subscribed to <pss/movement/+> and <pss/feedback>")
        mqttClient.publish(topic_feedback, "mov_connected", qos=1)


    def message_decoder(client, userdata, msg):
        message = msg.payload.decode(encoding='UTF-8')
        topic = msg.topic
        # Syncronize auto and manual

        if topic == "pss/movement/auto" and Check.manual is False:
            # Data from Huskylens, ex. "<direction>,<seconds>,<speed>"
            split = message.split(",")
            direction = split[0]
            seconds = float(split[1])
            speed = int(split[2])

            if direction == "forward":
                if Check.obstacle is False:
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
            speed = 60
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
                motors.left(speed + 10)
                pass
            elif direction == "right":
                print("MANUAL: right")
                motors.right(speed + 10)
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

        elif topic == topic_mov:
            if message == "obstacle":
                Check.obstacle = True
                motors.stop()
                print("OBSTACLE!")
            elif message == "free":
                Check.obstacle = False
                print("FREE TO MOVE!")

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


    mqttClient.on_connect = connect
    mqttClient.on_message = message_decoder
    mqttClient.will_set(topic_feedback, "mov_disconnected", qos=1, retain=False)
    # Connect to the MQTT server & loop forever.
    # CTRL-C will stop the program from running.
    mqttClient.connect(serverAddress, 1883)
    # mqttClient.loop_start()
    mqttClient.loop_forever()

except KeyboardInterrupt:
    if motors is not None:
        motors.tear_down()

    print("Terminating program...")
    print("Interrupted by keyboard.")
