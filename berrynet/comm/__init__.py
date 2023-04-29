# (TODO: get dynamic)
# 初始化 comm: client id, ip, 端口(在 comm_config) 中, pw, 三个回调函数
# 1. 建立连接(回调) 2. 发送消息(回调) 3. 接收消息(回调)

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from berrynet import logger
from logzero import setup_logger

# 1. comm_config: broker(dic) topic subscribe(dic) 2. device_config: client_id password
def on_message(client, userdata, msg):
    """Dispatch received message to its bound functor.
    """
    logger.debug('Receive message from topic {}'.format(msg.topic))
    # logger.debug('Message payload {}'.format(msg.payload))
    client.comm_config['subscribe'][msg.topic](msg.payload)


class Communicator(object):
    def __init__(self, comm_config, device_config, debug=False):
        self.client = mqtt.Client(device_config["client_id"])
        self.client.username_pw_set(device_config["password"])
        self.client.comm_config = comm_config

    def run(self):
        self.client.connect(
            self.client.comm_config['broker']['address'],
            self.client.comm_config['broker']['port'],
            60)

        self.client.loop_forever()

    def start_nb(self):
        def on_connect(client, userdata, flags, rc):
            logger.debug('Connected with result code ' + str(rc))

            for topic in client.comm_config['subscribe'].keys():
                logger.debug('Subscribe topic {}'.format(topic))
                client.subscribe(topic)

        self.client.on_connect = on_connect

        self.client.connect(
            self.client.comm_config['broker']['address'], self.client.comm_config['broker']['port'], 60)

        self.client.loop_start()

    def stop_nb(self):
        self.client.loop_stop()

    def send(self, topic, payload):
        self.run()

        # logger.debug('Send message to topic')

        test_payload = "{"
        test_payload += "\"Humidity\":2,";
        test_payload += "\"Temperature\":25";
        test_payload += "}"

        # TODO: test thingsboard
        self.client.publish("v1/devices/me/vedio", test_payload)
        print(payload)


def disconnect(self):
    self.client.disconnect()
