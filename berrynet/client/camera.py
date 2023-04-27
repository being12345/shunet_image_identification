# TODO: reconstruct args convert to json

import argparse
import json
import logging
import time

from datetime import datetime

import cv2

from berrynet import logger
from berrynet.comm import Communicator, payload


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--mode',
        default='stream',
        help='Camera creates frame(s) from stream or file. (default: stream)'
    )
    ap.add_argument(
        '--stream-src',
        type=str,
        default='0',
        help=('Camera stream source. '
              'It can be device node ID or RTSP URL. '
              '(default: 0)')
    )
    ap.add_argument(
        '--fps',
        type=float,
        default=1,
        help='Frame per second in streaming mode. (default: 1)'
    )
    ap.add_argument(
        '--filepath',
        default='',
        help='Input image path in file mode. (default: empty)'
    )
    ap.add_argument(
        '--broker-ip',
        default='localhost',
        help='MQTT broker IP.'
    )
    ap.add_argument(
        '--broker-port',
        default=1883,
        type=int,
        help='MQTT broker port.'
    )
    ap.add_argument('--topic',
                    default='berrynet/data/rgbimage',
                    help='The topic to send the captured frames.'
                    )
    ap.add_argument('--display',
                    action='store_true',
                    help=('Open a window and display the sent out frames. '
                          'This argument is only effective in stream mode.')
                    )
    ap.add_argument('--hash',
                    action='store_true',
                    help='Add md5sum of a captured frame into the result.'
                    )
    ap.add_argument('--meta',
                    type=str,
                    default='{}',
                    help='Metadata field for stringified JSON data.'
                    )
    ap.add_argument('--debug',
                    action='store_true',
                    help='Debug mode toggle'
                    )
    return vars(ap.parse_args())


def check_camera_type(args):
    # Check input stream source
    if args['stream_src'].isdigit():
        # source is a physically connected camera
        stream_source = int(args['stream_src'])
    else:
        # source is an IP camera
        stream_source = args['stream_src']

    return stream_source


def capture_stream_image(comm, metadata, args):
    # Check input stream source
    stream_source = check_camera_type(args)

    capture = cv2.VideoCapture(stream_source)

    cam_fps = capture.get(cv2.CAP_PROP_FPS)

    out_fps = args['fps']

    interval = set_interval(cam_fps, out_fps)

    log_stream_image(stream_source, cam_fps, out_fps, args, args['topic'])

    counter = 0
    fail_counter = 0

    while True:
        status, im = capture.read()
        if (status is True):
            counter = get_image_success(counter, interval, im, args)
            # comm_stream_image(im, metadata, args, comm)

        else:
            fail_counter = get_image_fail(fail_counter, capture, stream_source)
            capture = cv2.VideoCapture(stream_source)


def set_interval(cam_fps, out_fps):
    if cam_fps > 30 or cam_fps < 1:
        # logger.warn('Camera FPS is {} (>30 or <1). Set it to 30.'.format(cam_fps))
        cam_fps = 30
    interval = int(cam_fps / out_fps)

    return interval


def log_stream_image(stream_source, cam_fps, out_fps, interval, topic):
    logger.debug('===== VideoCapture Information =====')
    if type(stream_source) == "int":
        stream_source_uri = '/dev/video{}'.format(stream_source)
    else:
        stream_source_uri = stream_source
    logger.debug('Stream Source: {}'.format(stream_source_uri))
    logger.debug('Camera FPS: {}'.format(cam_fps))
    logger.debug('Output FPS: {}'.format(out_fps))
    logger.debug('Interval: {}'.format(interval))
    logger.debug('Send MQTT Topic: {}'.format(topic))
    logger.debug('====================================')


def get_image_success(counter, interval, im, args):
    counter += 1
    if counter == interval:
        logger.debug('Drop frames: {}'.format(counter - 1))
        counter = 0

        if args['display']:
            display_image(im, args)

        t = datetime.now()
        logger.debug('send: {} ms'.format(duration(t)))

    else:
        pass

    return counter


def display_image(im, args):
    cv2.imshow('Frame', im)
    cv2.waitKey(1)


def get_image_fail(fail_counter, capture, stream_source):
    fail_counter += 1
    logger.critical('ERROR: Failure #{} happened when reading frame'.format(fail_counter))

    # Re-create capture.
    capture.release()
    logger.critical('Re-create a capture and reconnect to {} after 5s'.format(stream_source))
    time.sleep(5)

    return fail_counter


def capture_file_image(args):
    im = cv2.imread(args['filepath'])
    retval, jpg_bytes = cv2.imencode('.jpg', im)
    return jpg_bytes


def comm_stream_image(im, metadata, args, comm):
    retval, jpg_bytes = cv2.imencode('.jpg', im)
    mqtt_payload = payload.serialize_jpg(jpg_bytes, args['hash'], metadata)
    comm.send(args['topic'], mqtt_payload)


def comm_file_image(jpg_bytes, args, metadata, comm):
    mqtt_payload = payload.serialize_jpg(jpg_bytes, args['hash'], metadata)

    logger.debug('payload: {} ms'.format(duration(datetime.now())))
    logger.debug('payload size: {}'.format(len(mqtt_payload)))

    # Client publishes payload
    comm.send(args['topic'], mqtt_payload)

    logger.debug('mqtt.publish: {} ms'.format(duration(datetime.now())))
    logger.debug('publish at {}'.format(datetime.now().isoformat()))


def duration(t):
    return (datetime.now() - t).microseconds / 1000


def main():
    args = parse_args()

    if args['debug']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    comm_config = {
        'subscribe': {},
        'broker': {
            'address': args['broker_ip'],
            'port': args['broker_port']
        }
    }

    comm = Communicator(comm_config, debug=True)

    metadata = json.loads(args.get('meta', '{}'))

    if args['mode'] == 'stream':
        capture_stream_image(comm, metadata, args)
    elif args['mode'] == 'file':
        jpg_bytes = capture_file_image(args)
        # comm_file_image(jpg_bytes, args, metadata, comm)
    else:
        logger.error('User assigned unknown mode {}'.format(args['mode']))


if __name__ == '__main__':
    main()
