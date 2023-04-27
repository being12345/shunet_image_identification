import json
from unittest import TestCase

from berrynet.client.camera import capture_stream_image, get_image_fail, capture_file_image, comm_file_image
from berrynet.comm import Communicator

class Test(TestCase):
    def test_capture_stream_image(self):
        args = {'mode': 'stream', 'stream_src': '0', 'fps': 6,
                'filepath': 'C:\\Users\\lizhuofeng\\Desktop\\BerryNet-image\\berrynet\\test\\camera_test.jpg'
            , 'display': '1'}
        actual = capture_stream_image(args)
        print(actual)

    def test_get_image_fail(self):
        get_image_fail(1, {}, 0)


class Comm_Test(TestCase):
    def test_comm_file_image(self):
        args = {'mode': 'file', 'stream_src': '0', 'fps': 1, 'filepath': 'C:\\Users\\lizhuofeng\\Desktop\\BerryNet-image\\berrynet\\test\\camera_test.jpg', 'broker_ip': 'localhost', 'broker_port': 1883, 'topic': 'berrynet/data/rgbimage', 'display': False, 'hash': False, 'meta': '{}', 'debug': False}
        comm_config = {
            'subscribe': {},
            'broker': {
                'address': args['broker_ip'],
                'port': args['broker_port']
            }
        }

        comm = Communicator(comm_config, debug=True)

        metadata = json.loads(args.get('meta', '{}'))
        jpg_bytes = capture_file_image(args)
        comm_file_image(jpg_bytes, args, metadata, comm)
