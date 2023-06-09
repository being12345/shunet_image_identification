import logging
import time

from argparse import ArgumentParser
from os import path

import cv2
import numpy as np
import tensorflow as tf

from berrynet.engine import DLEngine
from berrynet import logger


def parse_argsr():
    parser = ArgumentParser()
    parser.add_argument(
        "-e", "--engine",
        help=("Classifier or Detector engine. "
              "classifier, or detector is acceptable. "
              "(classifier by default)"),
        default="detector",
        type=str)
    parser.add_argument(
        "-m", "--model",
        help="Path to an .xml file with a trained model.",
        required=True,
        type=str)
    parser.add_argument(
        "-l", "--labels",
        help="Labels mapping file",
        default=None,
        type=str)
    parser.add_argument(
        "--top_k",
        help="Number of top results",
        default=3,
        type=int)
    parser.add_argument(
        "--num_threads",
        help="Number of threads",
        default=1,
        type=int)
    parser.add_argument(
        "-i", "--input",
        help="Path to a folder with images or path to an image files",
        required=True,
        type=str)
    parser.add_argument(
        "--debug",
        help="Debug mode toggle",
        default=False,
        action="store_true")

    return parser.parse_args()


# only reconstructed detector
class TFLiteDetectorEngine(DLEngine):
    def __init__(self, model, labels, threshold=0.5, num_threads=1):
        """
        Builds Tensorflow graph, load model and labels
        """
        # Load labels
        self.labels = self._load_label(labels)
        self.classes = len(self.labels)

        # Define lite graph and Load Tensorflow Lite model into memory
        self.interpreter = tf.lite.Interpreter(model_path=model, num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_dtype = self.input_details[0]['dtype']
        self.threshold = threshold

    def __delete__(self, instance):
        # tf.reset_default_graph()
        # self.sess = tf.InteractiveSession()
        del self.interpreter

    def process_input(self, tensor):
        """Resize and normalize image for network input"""

        self.img_w = tensor.shape[1]
        self.img_h = tensor.shape[0]

        frame = cv2.cvtColor(tensor, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (300, 300))
        frame = np.expand_dims(frame, axis=0)
        if self.input_dtype == np.float32:
            frame = (2.0 / 255.0) * frame - 1.0
            frame = frame.astype('float32')
        else:
            # default data type returned by cv2.imread is np.unit8
            pass
        return frame

    def inference(self, tensor):
        self.interpreter.set_tensor(self.input_details[0]['index'], tensor)
        self.interpreter.invoke()

        # get results
        boxes = self.interpreter.get_tensor(
            self.output_details[0]['index'])
        classes = self.interpreter.get_tensor(
            self.output_details[1]['index'])
        scores = self.interpreter.get_tensor(
            self.output_details[2]['index'])
        num = self.interpreter.get_tensor(
            self.output_details[3]['index'])
        return {
            'boxes': boxes,
            'classes': classes,
            'scores': scores,
            'num': num
        }

    def process_output(self, output):
        # get results
        boxes = np.squeeze(output['boxes'][0])
        classes = np.squeeze(output['classes'][0] + 1).astype(np.int32)
        scores = np.squeeze(output['scores'][0])
        num = output['num'][0]

        annotations = []
        number_boxes = boxes.shape[0]
        for i in range(number_boxes):
            box = tuple(boxes[i].tolist())
            ymin, xmin, ymax, xmax = box

            if scores[i] < self.threshold:
                continue
            annotations.append({
                'label': self.labels[classes[i]],
                'confidence': float(scores[i]),
                'left': int(xmin * self.img_w),
                'top': int(ymin * self.img_h),
                'right': int(xmax * self.img_w),
                'bottom': int(ymax * self.img_h)
            })
        return {'annotations': annotations}

    def _load_label(self, path):
        with open(path, 'r') as f:
            labels = list(map(str.strip, f.readlines()))
        return labels


"""
    engine 整合测试(没有通信模块) 
"""


def main():
    # Example command
    #     $ python3 tflite_engine.py -e detector \
    #           -m detect.tflite --labels labels.txt -i dog.jpg --debug
    args = parse_argsr()

    # if args.debug:
    #     logger.setLevel(logging.DEBUG)
    # else:
    #     logger.setLevel(logging.INFO)

    if args.engine == 'detector':
        engine = TFLiteDetectorEngine(
            model=args.model,
            labels=args.labels,
            num_threads=args.num_threads)
    else:
        raise Exception('Illegal engine {}, it should be '
                        'classifier or detector'.format(args.engine))

    for i in range(5):
        bgr_array = cv2.imread(args.input)
        t = time.time()
        image_data = engine.process_input(bgr_array)
        output = engine.inference(image_data)
        model_outputs = engine.process_output(output)
        # Reference result
        #     input:
        #         darknet/data/dog.jpg
        #     output:
        #         Inference takes 0.7533011436462402 s
        #         Inference takes 0.5741658210754395 s
        #         Inference takes 0.6120760440826416 s
        #         Inference takes 0.6191139221191406 s
        #         Inference takes 0.5809791088104248 s
        #         label: dog  conf: 0.869189441204071  (131, 218) (314, 539)
        logger.debug('Inference takes {} s'.format(time.time() - t))

    if args.engine == 'detector':
        for r in model_outputs['annotations']:
            logger.debug('label: {0}  conf: {1}  ({2}, {3}) ({4}, {5})'.format(
                r['label'],
                r['confidence'],
                r['left'],
                r['top'],
                r['right'],
                r['bottom']
            ))
    else:
        raise Exception('Can not get result '
                        'from illegal engine {}'.format(args.engine))


if __name__ == '__main__':
    main()
