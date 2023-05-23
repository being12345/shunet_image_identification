# (TODO: get ID dynamic)

# reconstructed by zhuofengli

import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from berrynet import logger
from logzero import setup_logger


def on_message(client, userdata, msg):
    """Dispatch received message to its bound functor.
    """
    logger.debug('Receive message from topic {}'.format(msg.topic))

    # call back used for inference
    client.comm_config['subscribe'][msg.topic](msg.payload)


class Communicator(object):
    """物联网协议通信类
    1. 初始化类: 必须提供 comm_config(通信相关配置), device_config(设备相关配置, 便于连接云平台), 具体实例见 main 函数
    2. 连接 broker (已设置 on_connect 回调) 并订阅 topic: 运行 start_nb, client 将以非阻塞形式收发消息(多线程)
    3. 发送消息: 运行 send
    4. 接受消息: 已设置 on_message 回调
    """

    def __init__(self, comm_config, device_config, debug=False):
        self.client = mqtt.Client(device_config["client_id"])
        self.client.username_pw_set(device_config["password"])
        self.client.comm_config = comm_config
        self.client.on_message = on_message

    # depulicated
    def run(self):
        self.client.connect(
            self.client.comm_config['broker']['address'],
            self.client.comm_config['broker']['port'],
            60)

        self.client.loop_forever()

    def start_nb(self):
        def on_connect(client, userdata, flags, rc):
            logger.debug('Connected with result code ' + str(rc))

            if 'subscribe' in client.comm_config:
                for topic in client.comm_config['subscribe'].keys():
                    logger.debug('Subscribe topic {}'.format(topic))
                    client.subscribe(topic)

        self.client.on_connect = on_connect

        self.client.connect(
            self.client.comm_config['broker']['address'], self.client.comm_config['broker']['port'], 60)

        self.client.loop_start()

    def stop_nb(self):
        self.client.loop_stop()

    def send(self, payload):
        logger.debug('Send message to topic {}'.format(self.client.comm_config["topic"]))

        self.client.publish(self.client.comm_config["topic"], payload)


def main():
    """
    MQTT 通信类整合测试, 包括连接, 收发消息
    Returns:

    """
    comm_config = {
        "broker": {
            "address": 'broker.emqx.io',
            "port": 1883
        },
        "topic": "/berrynet/image",
        "subscribe": {

        }
    }

    device_config = {
        "client_id": "ABC",
        "password": "oBMEfJgd3XhaqrX8eibm"
    }

    comm = Communicator(comm_config, device_config)
    comm.start_nb()
    while True:
        time.sleep(2)
        comm.send(1)


if __name__ == '__main__':
    main()
