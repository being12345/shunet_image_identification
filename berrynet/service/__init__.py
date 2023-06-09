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

"""Engine service is a bridge between incoming data and inference engine.
"""

import os
import this
import time

from datetime import datetime

from berrynet import logger
from berrynet.comm import Communicator
from berrynet.comm import payload


# 1. 初始化
class EngineService(object):
    def __init__(self, service_name, engine, comm_config, device_config):
        self.service_name = service_name
        self.engine = engine
        self.comm_config = comm_config
        self.device_config = device_config  # TODO: ?

        for topic, functor in self.comm_config['subscribe'].items():
            self.comm_config['subscribe'][topic] = eval(functor)
        self.comm_config['subscribe']['berrynet/data/rgbimage'] = self.inference  # TODO: ?
        self.comm = Communicator(self.comm_config, device_config, debug=True)

    def inference(self, pl):
        rgb_array, jpg_json = self.json_to_rgb(pl)

        t = datetime.now()
        model_outputs = self.engin_io(rgb_array)

        logger.debug('Result: {}'.format(model_outputs))
        logger.debug('Classification takes {} ms'.format(EngineService.duration(t)))

        # self.engine.cache_data('model_output', model_outputs)
        # self.engine.cache_data('model_output_filepath', output_name)
        # self.engine.save_cache()

        self.result_hook(self.generalize_result(jpg_json, model_outputs))

    def json_to_rgb(self, pl):
        t = datetime.now()
        logger.debug('payload size: {}'.format(len(pl)))
        logger.debug('payload type: {}'.format(type(pl)))

        jpg_json = payload.deserialize_payload(pl.decode('utf-8'))
        jpg_bytes = payload.destringify_jpg(jpg_json['bytes'])
        logger.debug('destringify_jpg: {} ms'.format(EngineService.duration(t)))

        t = datetime.now()
        rgb_array = payload.jpg2rgb(jpg_bytes)
        logger.debug('jpg2rgb: {} ms'.format(self.duration(t)))

        return [rgb_array, jpg_json]

    def engin_io(self, rgb_array):
        image_data = self.engine.process_input(rgb_array)
        output = self.engine.inference(image_data)
        model_outputs = self.engine.process_output(output)

        return model_outputs

    def generalize_result(self, eng_input, eng_output):
        eng_input.update(eng_output)
        return eng_input

    def result_hook(self, generalized_result):
        logger.debug('base result_hook')

    @staticmethod
    def duration(t):
        return (datetime.now() - t).microseconds / 1000

    # TODO: wrong
    def run(self, args):
        """Infinite loop serving inference requests"""
        self.engine.create()
        self.comm.start_nb()
