from unittest import TestCase

from berrynet.client.camera import capture_stream_image


class Test(TestCase):
    def test_capture_stream_image(self):
        args = {'mode': 'stream', 'stream_src': '0', 'fps': 6, 'filepath': 'C:\\Users\\lizhuofeng\\Desktop\\BerryNet-image\\berrynet\\test\\camera_test.jpg'
                , 'display': '1'}
        actual = capture_stream_image(args)
        print(actual)


