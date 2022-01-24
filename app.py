import sys
import json
from flask import Flask, render_template, Response, flash
import eventlet
from flask_mqtt import Mqtt
from flask_socketio import SocketIO, emit
from flask_bootstrap import Bootstrap
# import paho.mqtt.client as mqtt
import picamera
import cv2
import socket
import io

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'pissi-pissi'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_CLEAN_SESSION'] = True
socketio = SocketIO(app)

mqtt_client = Mqtt(app)
vc = cv2.VideoCapture(0)


class Check:
    manual = True


# PUBLISH AND SUBSCRIBE TOPICS
topic_feedback = "pss/feedback"

# PUBLISH TOPICS
topic_mode = "pss/movement/mode"
topic_rc = "pss/movement/manual"
topic_hl = "pss/huskylens"


@app.route('/')
def index():
    # check in which mode is the robot
    return render_template('manual.html')


def gen():
    """Video streaming generator function."""
    while True:
        rval, frame = vc.read()
        cv2.imwrite('t.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('t.jpg', 'rb').read() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@mqtt_client.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Client connected to broker with response code ", rc)
    mqtt_client.subscribe(topic_feedback)


@mqtt_client.on_message()
def on_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    # payload = message.payload.decode(encoding='UTF-8')
    print("Received message: ", data['payload'])

    # emit a mqtt_message event to the socket containing the message data
    socketio.emit('mqtt_message', data=data)


@mqtt_client.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)


@app.route('/forward')
def forward():
    mqtt_client.publish(topic_rc, "forward")
    print("Move forward")

    return Response(status=201)


@app.route('/left')
def left():
    mqtt_client.publish(topic_rc, "left")
    print("Move left")

    return Response(status=201)


@app.route('/right')
def right():
    mqtt_client.publish(topic_rc, "right")
    print("Move right")

    return Response(status=201)


@app.route('/backward')
def backward():
    mqtt_client.publish(topic_rc, "backward")
    print("Move backward")

    return Response(status=201)


@app.route('/stop')
def stop():
    mqtt_client.publish(topic_rc, "stop")
    print("Stop motors")

    return Response(status=201)


@app.route('/automated_mode')
def change_to_auto_mode():
    # Check if it is possible
    if Check.manual is True:
        mqtt_client.publish(topic_mode, "auto")
        print("Switch to auto")
        Check.manual = False

    return render_template('auto.html')


@app.route('/manual_mode')
def change_to_manual_mode():
    if Check.manual is not True:
        mqtt_client.publish(topic_mode, "manual")
        print("Switch to manual")
        Check.manual = True

    return render_template('manual.html')


if __name__ == '__main__':
    try:
        '''flask_client = mqtt.Client("Flask")
        # client.username_pw_set(username, password)
        flask_client.on_connect = on_connect
        flask_client.on_message = on_message
        flask_client.connect('localhost', 1883)
        flask_client.loop_start()'''

        socketio.run(app, host='0.0.0.0', port=80, use_reloader=False, debug=False)
        # mqtt_client.init_app(app)
        # app.run(port=80, host='0.0.0.0', threaded=True, debug=False)

    except KeyboardInterrupt:
        print("Interrupted by console")
        sys.exit(0)
