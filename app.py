import sys
import os
from flask import Flask, render_template, Response, flash, request, redirect
# import eventlet
# from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import picamera
import cv2
import socket
import io

# eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'pissi-pissi'
app.config['UPLOAD_FOLDER'] = "voice_files"
# app.config['TEMPLATES_AUTO_RELOAD'] = True
# socketio = SocketIO(app)

vc = cv2.VideoCapture(0)


class Check:
    manual = True


# flask_client = mqtt.Client("Flask")

# PUBLISH AND SUBSCRIBE TOPICS
topic_feedback = "pss/feedback"

# PUBLISH TOPICS
topic_mode = "pss/movement/mode"
topic_rc = "pss/movement/manual"
topic_hl = "pss/huskylens"


def on_connect(client, userdata, flags, rc):
    print("Client connected to broker with response code ", rc)
    flask_client.subscribe(topic_feedback)


def on_message(client, userdata, message):
    payload = message.payload.decode(encoding='UTF-8')
    print("Received message: ", payload)
    if payload == "object_visible":
        # flash("Your pet is now visible. Would you like to switch to automated mode?")
        # emit a mqtt_message event to the socket containing the message data
        alert = "object_visible"
        # socketio.emit('mqtt_message', alert=alert)
        print(alert)

    elif payload == "object_lost":
        # flash("Unfortunately, your pet got away from the robot.")
        alert = "object_lost"
        # socketio.emit('mqtt_message', alert=alert)
        print(alert)


def on_publish(client, userdata, result):
    print("Published to broker")
    pass


@app.route('/')
def index():
    # check in which mode is the robot
    return render_template('manual.html')


def gen():
    """Video streaming generator function."""
    while True:
        rval, frame = vc.read()
        if frame is None or rval is None:
            print("Frame/rval is none")
        cv2.imwrite('/home/pi/Projects/PetSurveilanceSystem/t.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('/home/pi/Projects/PetSurveilanceSystem/t.jpg', 'rb').read() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/forward')
def forward():
    flask_client.publish(topic_rc, "forward")
    print("Move forward")

    return Response(status=201)


@app.route('/left')
def left():
    flask_client.publish(topic_rc, "left")
    print("Move left")

    return Response(status=201)


@app.route('/right')
def right():
    flask_client.publish(topic_rc, "right")
    print("Move right")

    return Response(status=201)


@app.route('/backward')
def backward():
    flask_client.publish(topic_rc, "backward")
    print("Move backward")

    return Response(status=201)


@app.route('/stop')
def stop():
    flask_client.publish(topic_rc, "stop")
    print("Stop motors")

    return Response(status=201)


@app.route('/automated_mode')
def change_to_auto_mode():
    # Check if it is possible
    if Check.manual is True:
        flask_client.publish(topic_mode, "auto")
        flask_client.publish(topic_hl, "start")
        print("Switch to auto")
        Check.manual = False

    return render_template('auto.html')


@app.route('/manual_mode')
def change_to_manual_mode():
    if Check.manual is not True:
        flask_client.publish(topic_mode, "manual")
        flask_client.publish(topic_hl, "sleep")
        print("Switch to manual")
        Check.manual = True

    return render_template('manual.html')


@app.route('/save-record', methods=['POST'])
def save_record():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    file_name = "voice.wav"
    full_file_name = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(full_file_name)
    return '<h1>Success</h1>'


if __name__ == '__main__':
    flask_client = mqtt.Client("Flask")
    # client.username_pw_set(username, password)
    flask_client.on_connect = on_connect
    flask_client.on_message = on_message
    flask_client.on_publish = on_publish
    flask_client.connect('localhost', 1883)
    flask_client.loop_start()
    app.run(port=8080, host='0.0.0.0', threaded=True, debug=False)

