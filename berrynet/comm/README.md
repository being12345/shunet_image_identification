# 物联网协议通信类
## what
此类用于为其他类提供通信服务, 将此类注入可以实现订阅, 发布相关 topic, 已达到不同层级传递数据的目的, 可以有效实现不同层之间数据传递的解耦。
## 前置知识(必学)
1. 理解 mqtt 协议 python 相关的基本 api: `connect`, `subscribe`, `send`
2. 理解回调函数在 `mqtt` 代码中的使用: `on_connect`, `on_message`等
3. 理解`loop_start()`等 loop 类函数实现机制: 多线程 + 缓冲
## how to use
1. 参考`main` 以及`./demo/mqtt.py`函数中的用例, 仔细设置相关`comm_config`(通信参数)以及`device_config`(设备参数)