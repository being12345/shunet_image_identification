# tflite engine
## what
本类是图像推理的底层实现(后续的`service.py`是对于其的进一步封装), 其实现的是: 接收一张图像, 使用模型推理出相关参数
## 前置知识
1. tensoflow 的基本使用(网上寻找例程)
2. 参数解析`parse_argsr`的使用
## 如何使用
1. 仔细阅读相关函数(尤其是函数名)以及`parse_argsr`中参数的说明
2. 运行`main`例程