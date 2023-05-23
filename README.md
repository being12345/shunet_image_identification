# 一种简易高拓展的图像识别程序
## 项目描述
**本程序从外部读入图像, 进行推理, 识别结果将通过`mqtt`协议传输**
## 使用技术栈
1. mqtt 
2. OpenCV
3. tflite
## 特点
1. 低耦合, 高拓展: 模块功能分明, 不同模块之间几乎没有耦合, 二者之间的交流均通过`mqtt`, 非常便于二次开发
2. 传输速度快: 采用`mqtt`多线程 + `buffer` 形式
3. 代码结构分明: 本程序是对于`clean_code`的实践
4. 代码经过重构后结构简单极易上手
## 参考书籍
在二次开发该项目之前, 建议首先阅读以下书籍

(重构（第2版）)[https://book.douban.com/subject/30468597/]

## 参考项目
(Berrynet)https://github.com/DT42/BerryNet
## 可考虑的后续开发
1. 添加dashboard
2. 移植到嵌入式设备中
...
## 致谢
thanks to my tutor Jun Han, giving me lots of encourage, resource and idea
thanks to opensourcecode, giving me the chance to learn
