import sys
import os
import uuid

from flask import Flask, render_template, Response, flash, request, redirect, url_for
from flask_login import login_user, login_required, current_user, logout_user
from database import db_session, init_db
from login import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
import picamera
import cv2
import requests
import logging
from clients.flask_client import topic_feedback, topic_rc, topic_mode, init_mqtt, start_loop, flask_client, Check

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pissi-pissi'
app.config['UPLOAD_FOLDER'] = "voice_files"

login_manager.init_app(app)
init_db()
init_mqtt()


@app.teardown_appcontext
def shutdown_context(exception=None):
    db_session.remove()


vc = cv2.VideoCapture(0)


class CheckManual:
    manual = True


access_key = "gain_access"
'''
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
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    # print("Received message: ", data['payload'])
    app.logger.info('Received message')

    if data['payload'] == "object_visible":
        Check.visible = True

    elif data['payload'] == "object_lost":
        Check.visible = False

    elif data['payload'] == "hl_connected":
        Check.hl_available = True
        app.logger.info('HL connected')

    elif data['payload'] == "hl_disconnected":
        Check.hl_available = False
        app.logger.info('HL disconnected')

    elif data['payload'] == "mov_connected":
        Check.mov_available = True
        app.logger.info('Movement connected')

    elif data['payload'] == "mov_disconnected":
        Check.mov_available = False
        app.logger.info('Movement disconnected')


def on_publish(client, userdata, result):
    print("Published to broker")
    app.logger.info('Published to broker')
    pass


flask_client = mqtt.Client("Flask")
# client.username_pw_set(username, password)
flask_client.on_connect = on_connect
flask_client.on_message = on_message
flask_client.on_publish = on_publish
flask_client.connect('localhost', 1883)
'''

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %('
                                                                       f'threadName)s : %(message)s')


@app.route('/')
def index():
    if 'id' in current_user.__dict__:
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))

    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in current_user.__dict__:
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))

    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        # remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password. Please, try again.')
            return redirect(url_for('login'))

        user.login_id = str(uuid.uuid4())
        db_session.commit()
        login_user(user)
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'login_id' in current_user.__dict__:
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))

    if request.method == 'GET':
        return render_template('signup.html')
    else:
        username = request.form['username']
        temp_user = User.query.filter_by(username=username).first()
        if temp_user:
            flash('Username already exists')
            return redirect(url_for('signup'))

        password = generate_password_hash(request.form['password'], method='sha256')
        a_key = request.form['access_key']

        if a_key != access_key:
            flash('Wrong access key, try again.')
            return redirect(url_for('signup'))

        user = User(username=username, password=password)

        db_session.add(user)
        db_session.commit()

        flash("You were successfully signed up!")
        return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()

    return redirect(url_for('index'))


def gen():
    """Video streaming generator function."""
    while True:
        rval, frame = vc.read()
        if frame is None or rval is None:
            print("Frame/rval is none")
            continue
        cv2.imwrite('/home/pi/Projects/PetSurveilanceSystem/t.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('/home/pi/Projects/PetSurveilanceSystem/t.jpg',
                                                          'rb').read() + b'\r\n')


@app.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/forward')
@login_required
def forward():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "forward")
        print("Move forward")
        app.logger.info('Move forward')

        return Response(status=201)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=200)


@app.route('/left')
@login_required
def left():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "left")
        print("Move left")
        app.logger.info('Move left')

        return Response(status=201)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=200)


@app.route('/right')
@login_required
def right():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "right")
        print("Move right")
        app.logger.info('Move right')

        return Response(status=201)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=200)


@app.route('/backward')
@login_required
def backward():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "backward")
        print("Move backward")
        app.logger.info('Move backward')

        return Response(status=201)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=200)


@app.route('/stop')
@login_required
def stop():
    flask_client.publish(topic_rc, "stop")
    print("Stop motors")
    app.logger.info('Stop motors')

    return Response(status=201)


'''
@app.route('/take_photo')
@login_required
def take_photo():
    flask_client.publish(topic_hl, "take_photo")
    print("Taking photo")
    app.logger.info('Taking photo')

    return Response(status=201)
'''


@app.route('/check_status')
def check():
    if CheckManual.manual is True and Check.visible is True and Check.hl_available is True:
        app.logger.info('Switch to auto (AJAX)')
        print('Switch to auto (AJAX)')
        CheckManual.manual = False
        flask_client.publish(topic_mode, "auto")
        return "visible"
    elif CheckManual.manual is False and Check.visible is False:
        app.logger.info('Switch to manual (AJAX)')
        print('Switch to manual (AJAX)')
        CheckManual.manual = True
        flask_client.publish(topic_mode, "manual")
        return "not_visible"

    return Response(status=200)


@app.route('/automated_mode')
@login_required
def change_to_auto_mode():
    if Check.hl_available is True:
        if CheckManual.manual is True:
            flask_client.publish(topic_mode, "auto")
            # flask_client.publish(topic_hl, "start")
            print("Switch to auto")
            app.logger.info('Switch to auto')

        CheckManual.manual = False
        return render_template('auto.html', name=current_user.username)
    else:
        flash("There is something wrong with the module, responsible for object tracking.")
        return redirect(url_for('change_to_manual_mode'))


@app.route('/manual_mode')
@login_required
def change_to_manual_mode():
    if CheckManual.manual is not True:
        flask_client.publish(topic_mode, "manual")
        # flask_client.publish(topic_hl, "sleep")
        print("Switch to manual")
        app.logger.info('Switch to manual')

    CheckManual.manual = True
    return render_template('manual.html', name=current_user.username)


'''
@app.route('/save-record', methods=['POST'])
@login_required
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
'''

if __name__ == '__main__':
    start_loop()
    app.run(port=8080, host='0.0.0.0', threaded=True, debug=False)
