from flask import Flask, render_template, Response
import paho.mqtt.client as mqtt
import picamera
import cv2
import socket
import io

# from flask_mqtt import Mqtt

app = Flask(__name__)

'''app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
# app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = True

mqtt_client = Mqtt()'''
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


def on_connect(client, userdata, flags, rc):
    print("Client connected to broker with response code ", rc)
    flask_client.subscribe(topic_feedback)


def on_message(client, userdata, message):
    payload = message.payload.decode(encoding='UTF-8')
    print("Received message: ", payload)
    pass


@app.route('/forward')
def forward():
    flask_client.publish(topic_rc, "forward")
    print("Move forward")
    pass


@app.route('/left')
def left():
    flask_client.publish(topic_rc, "left")
    print("Move left")
    pass


@app.route('/right')
def right():
    flask_client.publish(topic_rc, "right")
    print("Move right")
    pass


@app.route('/backward')
def backward():
    flask_client.publish(topic_rc, "backward")
    print("Move backward")
    pass


@app.route('/stop')
def stop():
    flask_client.publish(topic_rc, "stop")
    print("Stop motors")
    pass


@app.route('/change_to_auto_mode')
def change_to_auto_mode():
    # Check if it is possible
    if Check.manual is True:
        flask_client.publish(topic_mode, "auto")
        print("Switch to auto")
        Check.manual = False
        return render_template('auto.html')


@app.route('/change_to_manual_mode')
def change_to_manual_mode():
    if Check.manual is not True:
        flask_client.publish(topic_mode, "manual")
        print("Switch to manual")
        Check.manual = True
        return render_template('manual.html')


if __name__ == '__main__':
    flask_client = mqtt.Client("Flask")
    # client.username_pw_set(username, password)
    flask_client.on_connect = on_connect
    flask_client.on_message = on_message
    flask_client.connect('localhost', 1883)
    flask_client.loop_start()

    app.run(port=80, host='0.0.0.0', threaded=True)
    # mqtt_client.init_app(app)
