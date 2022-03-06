import paho.mqtt.client as mqtt

# PUBLISH AND SUBSCRIBE TOPICS
topic_feedback = "pss/feedback"

# PUBLISH TOPICS
topic_mode = "pss/movement/mode"
topic_rc = "pss/movement/manual"
topic_hl = "pss/huskylens"


class Check:
    visible = None
    hl_available = None
    mov_available = None


global flask_client


def on_connect(client, userdata, flags, rc):
    print("Client connected to broker with response code ", rc)
    flask_client.subscribe(topic_feedback)


def on_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    # print("Received message: ", data['payload'])
    # app.logger.info('Received message')

    if data['payload'] == "object_visible":
        Check.visible = True

    elif data['payload'] == "object_lost":
        Check.visible = False

    elif data['payload'] == "hl_connected":
        Check.hl_available = True

    elif data['payload'] == "hl_disconnected":
        Check.hl_available = False

    elif data['payload'] == "mov_connected":
        Check.mov_available = True

    elif data['payload'] == "mov_disconnected":
        Check.mov_available = False


def on_publish(client, userdata, result):
    print("Published to broker")
    pass


def init_mqtt():
    flask_client = mqtt.Client("Flask")
    # client.username_pw_set(username, password)
    flask_client.on_connect = on_connect
    flask_client.on_message = on_message
    flask_client.on_publish = on_publish
    flask_client.connect('localhost', 1883)

    # return flask_client


def start_loop():
    flask_client.loop_start()

