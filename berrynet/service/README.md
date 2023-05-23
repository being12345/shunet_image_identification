# tensorflowlite service
## what
`tensorflowlite service`订阅从`camera`的topic, 获取图像, 传递给 `tflite_engine` 获取的推理结果, 进一步加工并将该包装结果发送出去
## 前置知识
1. 理解`parse_args`运行逻辑
## how to use
1. 仔细阅读`parse_args`中的相关参数说明
2. 运行`main`例程