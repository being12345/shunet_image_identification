#!/usr/bin/python3
#
# Copyright 2018 DT42
#
# This file is part of BerryNet.
#
# BerryNet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BerryNet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BerryNet.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import json
import logging
import time

from datetime import datetime

import cv2

from berrynet import logger


# from berrynet.comm import Communicator
# from berrynet.comm import payload


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
        default=5,
        help='Frame per second in streaming mode. (default: 5)'
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


def main():
    args = parse_args()
    if args['debug']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # TODO: right?
    # comm_config = {
    #     'subscribe': {},
    #     'broker': {
    #         'address': args['broker_ip'],
    #         'port': args['broker_port']
    #     }
    # }
    #
    # comm = Communicator(comm_config, debug=True)

    metadata = json.loads(args.get('meta', '{}'))

    if args['mode'] == 'stream':
        capture_file_image(args)
    elif args['mode'] == 'file':
        [retval, jpg_bytes] = capture_file_image(args)
        comm_file_image(jpg_bytes)
    else:
        logger.error('User assigned unknown mode {}'.format(args['mode']))


def check_camera_type(args):
    # Check input stream source
    if args['stream_src'].isdigit():
        # source is a physically connected camera
        stream_source = int(args['stream_src'])
    else:
        # source is an IP camera
        stream_source = args['stream_src']

    return stream_source


def set_interval(cam_fps, args):
    if cam_fps > 30 or cam_fps < 1:
        # logger.warn('Camera FPS is {} (>30 or <1). Set it to 30.'.format(cam_fps))
        cam_fps = 30
    out_fps = args['fps']
    interval = int(cam_fps / out_fps)   # TODO: quick or slow depend this

    return interval



def capture_stream_image(args):
    counter = 0
    fail_counter = 0

    # Check input stream source
    stream_source = check_camera_type(args)

    capture = cv2.VideoCapture(stream_source)

    cam_fps = capture.get(cv2.CAP_PROP_FPS)

    interval = set_interval(cam_fps, args)

    # TODO: used for log
    # logger.debug('===== VideoCapture Information =====')
    # if type(stream_source) == "int":
    #     stream_source_uri = '/dev/video{}'.format(stream_source)
    # else:
    #     stream_source_uri = stream_source
    # logger.debug('Stream Source: {}'.format(stream_source_uri))
    # logger.debug('Camera FPS: {}'.format(cam_fps))
    # logger.debug('Output FPS: {}'.format(out_fps))
    # logger.debug('Interval: {}'.format(interval))
    # logger.debug('Send MQTT Topic: {}'.format(args['topic']))
    # logger.debug('Warmup Counter: {}'.format(warmup_counter))
    # logger.debug('====================================')

    while True:
        status, im = capture.read()
        if status is True:
            counter += 1
            if counter == interval:
                logger.debug('Drop frames: {}'.format(counter - 1))

                # Open a window and display the ready-to-send frame.
                # This is useful for development and debugging.
                if args['display']:
                    cv2.imshow('Frame', im)
                    cv2.waitKey(1)

                t = datetime.now()
                retval, jpg_bytes = cv2.imencode('.jpg', im)
                # mqtt_payload = payload.serialize_jpg(jpg_bytes, args['hash'], metadata)
                # comm.send(args['topic'], mqtt_payload)
                logger.debug('send: {} ms'.format(duration(t)))
            else:
                pass
        else:
            fail_counter += 1
            logger.critical('ERROR: Failure #{} happened when reading frame'.format(fail_counter))

            # Re-create capture.
            capture.release()
            logger.critical('Re-create a capture and reconnect to {} after 5s'.format(stream_source))
            time.sleep(5)
            capture = cv2.VideoCapture(stream_source)


def capture_file_image(args):
    im = cv2.imread(args['filepath'])
    retval, jpg_bytes = cv2.imencode('.jpg', im)
    return [retval, jpg_bytes]


def comm_file_image(jpg_bytes):
    return
    # mqtt_payload = payload.serialize_jpg(jpg_bytes, args['hash'], metadata)
    # logger.debug('payload: {} ms'.format(duration(t)))
    # logger.debug('payload size: {}'.format(len(mqtt_payload)))
    #
    # # Client publishes payload
    # t = datetime.now()
    # comm.send(args['topic'], mqtt_payload)
    # logger.debug('mqtt.publish: {} ms'.format(duration(t)))
    # logger.debug('publish at {}'.format(datetime.now().isoformat()))


def duration(t):
    return (datetime.now() - t).microseconds / 1000


if __name__ == '__main__':
    main()
