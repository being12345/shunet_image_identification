"""Engine service is a bridge between incoming data and inference engine.
"""
# 1. 修改模型路径(在参数中指定)
import argparse
from datetime import datetime
import logging
import this
import time
from turtle import color

from berrynet import logger
from berrynet.comm import payload
from berrynet.dlmodelmgr import DLModelManager
from berrynet.engine.tflite_engine import TFLiteDetectorEngine
from berrynet.service import EngineService
from berrynet.utils import draw_bb, draw_label
from berrynet.utils import generate_class_color


class TFLiteDetectorService(EngineService):
    def __init__(self, service_name, engine, comm_config, device_config, draw=False):
        super(TFLiteDetectorService, self).__init__(service_name,
                                                    engine,
                                                    comm_config,
                                                    device_config)
        self.draw = draw

    def inference(self, pl):
        bgr_array, jpg_json = self.json_to_bgr(pl)

        t2 = time.time()
        model_outputs = self.engin_io(bgr_array)
        logger.debug('Result: {}'.format(model_outputs))
        logger.debug('Detection takes {} ms'.format(time.time() - t2))

        classes = self.engine.classes
        labels = self.engine.labels

        logger.debug('draw = {}'.format(self.draw))
        if self.draw is False:
            self.result_hook(self.generalize_result(jpg_json, model_outputs))
        else:
            self.result_hook(
                draw_bb(bgr_array,
                        self.generalize_result(jpg_json, model_outputs),
                        generate_class_color(class_num=classes),
                        labels))

    def json_to_bgr(self, pl):
        t = datetime.now()
        logger.debug('payload size: {}'.format(len(pl)))
        logger.debug('payload type: {}'.format(type(pl)))

        jpg_json = payload.deserialize_payload(pl.decode('utf-8'))
        jpg_bytes = payload.destringify_jpg(jpg_json['bytes'])
        logger.debug('destringify_jpg: {} ms'.format(EngineService.duration(t)))

        t = datetime.now()
        bgr_array = payload.jpg2bgr(jpg_bytes)
        logger.debug('jpg2bgr: {} ms'.format(self.duration(t)))

        return [bgr_array, jpg_json]

    def result_hook(self, generalized_result):
        logger.debug('result_hook, annotations: {}'.format(generalized_result['annotations']))
        self.comm.send(payload.serialize_payload(generalized_result))


def get_model_config(args):
    dlmm = DLModelManager()
    meta = dlmm.get_model_meta(args['model_package'])
    args['model'] = meta['model']
    args['label'] = meta['label']


def log_model(args):
    """
    log model and label path
    """
    if args['model']:
        logger.debug('model filepath: ' + args['model'])
        logger.debug('label filepath: ' + args['label'])
    else:
        raise Exception('need model')


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-s', '--service',
        help=('Classifier or Detector service. '
              'classifier, or detector is acceptable. '
              '(classifier by default)'),
        default='detector',
        type=str)
    ap.add_argument(
        '--service_name',
        default='tflite_classifier',
        help='Human-readable service name for service management.')
    ap.add_argument(
        '-m', '--model',
        help='Model file path')
    ap.add_argument(
        '-l', '--label',
        help='Label file path')
    ap.add_argument(
        '-p', '--model_package',
        default='',
        help='Model package name. Find model and label file paths automatically.')
    ap.add_argument(
        '--top_k',
        help='Display top K classification results.',
        default=3,
        type=int)
    ap.add_argument(
        '--num_threads',
        default=1,
        help="Number of threads for running inference.",
        type=int)
    ap.add_argument(
        '--draw',
        action='store_true',
        help='Draw bounding boxes on image in result')
    ap.add_argument(
        '--debug',
        action='store_true',
        help='Debug mode toggle')
    ap.add_argument(
        '--broker-ip',
        default='broker.emqx.io',
        help='MQTT broker IP.'
    )
    ap.add_argument(
        '--broker-port',
        default=1883,
        type=int,
        help='MQTT broker port.'
    )
    ap.add_argument('--topic',
                    default='shunet/inference',
                    help='The topic to send the captured frames.'
                    )

    ap.add_argument(
        '--send-ip',
        default='demo.thingsboard.io',
        help='MQTT broker IP.'
    )
    ap.add_argument(
        '--send-port',
        default=1883,
        help='MQTT broker IP.'
    )
    ap.add_argument('--clientId',
                    default='inference',
                    help='cloud platform token'
                    )
    ap.add_argument('--password',
                    default='Sl2y3k68WQnpBOLPQ9AE',
                    help='password'
                    )
    return vars(ap.parse_args())


def main():
    # Comm_Test TFLite engines
    args = parse_args()
    # if args['debug']:
    #     logger.setLevel(logging.DEBUG)
    # else:
    #     logger.setLevel(logging.INFO)

    if args['model_package'] != '':
        get_model_config(args)

    log_model(args)

    comm_config = {
        'subscribe': {},
        'broker': {
            "address": args.get('broker_ip'),
            "send_address": args.get('send_ip'),
            "port": args.get('broker_port')
        },
        'topic': args.get('topic'),
    }

    device_config = {
        "client_id": args['clientId'],
        "password": args['password']
    }

    if args['service'] == 'detector':
        engine = TFLiteDetectorEngine(
            model=args['model'],
            labels=args['label'],
            num_threads=args['num_threads'])

        service_functor = TFLiteDetectorService
    else:
        raise Exception('Illegal service {}, it should be classifier or detector'.format(args['service']))

    engine_service = service_functor(args['service_name'],
                                     engine,
                                     comm_config,
                                     device_config,
                                     draw=args['draw'])

    engine_service.run(args)

    while True:
        continue


if __name__ == '__main__':
    main()
