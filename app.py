from datetime import datetime
import sys
import os
import uuid
import sqlalchemy
from flask import Flask, render_template, Response, flash, request, redirect, url_for
from flask_login import login_user, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.datastructures import ImmutableDict
from database import db_session, init_db
from login import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Photo
import picamera
import cv2
import requests
import logging
from clients.flask_client import topic_feedback, topic_rc, topic_mode, \
    topic_motors_power, topic_camera_movement, topic_camera_setting, init_mqtt, Check
from werkzeug.middleware.shared_data import SharedDataMiddleware
from clients import motorslib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pissi-pissi'
app.config['UPLOAD_FOLDER'] = './uploads'

access_key = "gain_access"
login_manager.init_app(app)
init_db()
flask_client = init_mqtt()
csrf = CSRFProtect(app)

app.add_url_rule('/uploads/<filename>', 'uploaded_file', build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads': app.config['UPLOAD_FOLDER']
})

# Enabling Jinja2 Engine to auto escape all input JavaScript codes
jinja_options = ImmutableDict(
    extensions=[
        'jinja2.ext.autoescape', 'jinja2.ext.with_'
    ])

app.jinja_env.autoescape = True


@app.teardown_appcontext
def shutdown_context(exception=None):
    db_session.remove()


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('error.html', reason=e.description), 400


vc = cv2.VideoCapture(0)


class CheckManual:
    manual = True


class MotorsState:
    on = False


logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %('
                                                                       f'threadName)s : %(message)s')


@app.route('/')
def index():
    if 'id' in current_user.__dict__:
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))

    return render_template('index.html'), 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in current_user.__dict__:
        if CheckManual.manual is True:
            return redirect(url_for('change_to_manual_mode'))
        else:
            return redirect(url_for('change_to_auto_mode'))

    if request.method == 'GET':
        return render_template('login.html'), 200
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

        user = User(username=username, password=password, center_camera_choice=True, auto_switch_choice=True)

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
        if rval is None:
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
        app.logger.info('Move forward')

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/left')
@login_required
def left():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "left")
        app.logger.info('Move left')

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/right')
@login_required
def right():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "right")
        app.logger.info('Move right')

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/backward')
@login_required
def backward():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "backward")
        app.logger.info('Move backward')

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/stop')
@login_required
def stop():
    if Check.mov_available is True:
        flask_client.publish(topic_rc, "stop")
        app.logger.info('Stop motors')

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/snap')
@login_required
def take_photo():
    rval, frame = vc.read()
    if rval:
        app.logger.info('Taking photo')

        filename = str(uuid.uuid4()) + '.jpg'
        cv2.imwrite(f'./uploads/{filename}', frame)

        new_photo = Photo(location=f'/uploads/{filename}', name=filename, created_at=datetime.now(),
                          user_id=current_user.id)
        db_session.add(new_photo)
        db_session.commit()

        return Response(status=200)

    else:
        app.logger.info('Unable to take photo')
        return Response(status=500)


@app.route('/check_status')
@login_required
def check():
    if Check.hl_available is True:
        if CheckManual.manual is True and Check.visible is True and current_user.auto_switch_choice is True:
            app.logger.info('Switch to auto (AJAX)')
            CheckManual.manual = False
            flask_client.publish(topic_mode, "auto")

            return "visible"
        elif CheckManual.manual is False and Check.visible is False:
            app.logger.info('Switch to manual (AJAX)')
            CheckManual.manual = True
            flask_client.publish(topic_mode, "manual")

            return "not_visible"

        return Response(status=200)

    else:
        return Response(status=500)


@app.route('/automated_mode')
@login_required
def change_to_auto_mode():
    if Check.hl_available is True:
        if CheckManual.manual is True:
            flask_client.publish(topic_mode, "auto")
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
        app.logger.info('Switch to manual')

    CheckManual.manual = True
    return render_template('manual.html', name=current_user.username)


@app.route('/gallery')
@login_required
def gallery():
    first_image = Photo.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Photo.created_at)).first()
    images = Photo.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Photo.created_at)).all()

    return render_template('gallery.html', Photo=Photo, first_image=first_image, images=images,
                           name=current_user.username), 200


@app.route('/gallery/delete/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def delete_photo(photo_id):
    image_to_delete = Photo.query.filter_by(id=photo_id).first()

    new_first_image = Photo.query.filter_by(
        user_id=current_user.id).order_by(sqlalchemy.desc(Photo.created_at)).first()
    new_images = Photo.query.filter_by(user_id=current_user.id).order_by(
        sqlalchemy.desc(Photo.created_at)).all()

    if request.method == 'POST':
        pass
    else:
        if image_to_delete.user_id != current_user.id:
            pass

        else:
            db_session.delete(image_to_delete)
            db_session.commit()

            new_first_image = Photo.query.filter_by(
                user_id=current_user.id).order_by(sqlalchemy.desc(Photo.created_at)).first()
            new_images = Photo.query.filter_by(user_id=current_user.id).order_by(
                sqlalchemy.desc(Photo.created_at)).all()

    return redirect(url_for('gallery', Photo=Photo, first_image=new_first_image, images=new_images,
                            name=current_user.username))


@app.route('/gallery/rename/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def rename(photo_id):
    if request.method == 'GET':
        pass
    else:
        new_name = request.form['new_name']
        temp_photo = Photo.query.filter_by(name=new_name).first()
        if temp_photo:
            flash(f'A photo with the name {new_name} already exists!')
            return redirect(url_for('gallery'))

        # CHECK SIZE OF THE NAME
        if len(new_name) < 5:
            flash('Invalid name - it must be more than 4 symbols long!.')
            return redirect(url_for('gallery'))

        image_to_rename = Photo.query.filter_by(id=photo_id).first()
        image_to_rename.name = new_name

        db_session.commit()

        return redirect(url_for('gallery'))


@app.route('/motors_power', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def motors_on():
    if request.method == 'GET':
        if MotorsState.on is True:
            return "on"
        else:
            return "off"
    else:
        if Check.mov_available is True:
            if MotorsState.on is False:
                app.logger.info('Motors on')
                flask_client.publish(topic_motors_power, "on")
                MotorsState.on = True
                return "on"
            else:
                app.logger.info('Motors off')
                flask_client.publish(topic_motors_power, "off")
                MotorsState.on = False
                return "off"

        else:
            return Response(status=500)


@app.route('/auto_switch_setting', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def auto_switch():
    if request.method == 'GET':
        if current_user.auto_switch_choice is True:
            return "checked"
        else:
            return "unchecked"
    else:
        if current_user.auto_switch_choice is False:
            app.logger.info('Auto switch on')
            current_user.auto_switch_choice = True
            db_session.commit()

            return "checked"

        else:
            app.logger.info('Auto switch off')
            current_user.auto_switch_choice = False
            db_session.commit()

            return "unchecked"


@app.route('/camera_setting', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def camera_center():
    if Check.mov_available is True:
        if request.method == 'GET':
            if current_user.center_camera_choice is True:
                flask_client.publish(topic_camera_setting, "check")
                return "checked"
            else:
                flask_client.publish(topic_camera_setting, "uncheck")
                return "unchecked"

        else:
            if current_user.center_camera_choice is False:
                app.logger.info('Camera center on')
                flask_client.publish(topic_camera_setting, "check")
                current_user.center_camera_choice = True
                db_session.commit()

                return "checked"
            else:
                app.logger.info('Camera center off')
                flask_client.publish(topic_camera_setting, "uncheck")
                current_user.center_camera_choice = False
                db_session.commit()

                return "unchecked"

    else:
        return Response(status=500)


@app.route('/camera/left')
@login_required
def camera_left():
    if Check.mov_available is True:
        app.logger.info('Camera left')
        flask_client.publish(topic_camera_movement, "left")

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/camera/right')
@login_required
def camera_right():
    if Check.mov_available is True:
        app.logger.info('Camera right')
        flask_client.publish(topic_camera_movement, "right")

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


@app.route('/camera/stop')
@login_required
def camera_stop():
    if Check.mov_available is True:
        app.logger.info('Camera stop')
        flask_client.publish(topic_camera_movement, "stop")

        return Response(status=200)
    else:
        flash("There is something wrong with the module, responsible for movement.")
        return Response(status=500)


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
    flask_client.loop_start()
    try:
        app.run(port=8080, host='0.0.0.0', threaded=True, debug=False)
    finally:
        motorslib.tear_down()
