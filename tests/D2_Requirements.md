# D2 要求：

## 1. 模式扩展

D2 要求新增：AOOR, VOOR, AAIR, VVIR，需要添加到面板里面，同时，开放新的所需参数（这个已经 mode_config.py 里面，同时给新增的参数设置默认值。这些新增的模式也必须遵守之前 D1 的设计，即必须能在下拉菜单里面选择，同时也能遵守相应的 stepping mode（需要在 mode_config 里面去撰写新的 stepping function，以及相应的接口。

新增参数：
![alt text](image.png)
新增 A 和 V sensitivity，然后 Pulse width 和 amplitude 需要修改范围。

## 2. serial communication

DCM 可以向 pacemaker 发送指令和传输数据，并且接收从 pacemaker 传回来的数据和 Egram。要修改 load 的功能，使其不仅可以从 data 上载到 DCM，还可以传到 pacemaker 板里面。

## 3. 参数的设置、存储、传输与“回读校验”闭环

可以比较和检查 DCM 里面和板子里参数是否一致。

## 4. 参数范围变化

详情见 1

## 5. Egram 需要实时演示

实时读取信号

## 6. 文档化“参数从 DCM 到设备”的全链路与数据类型论证

说明参数如何在 DCM 产生、如何打包、通信、设备存储与回读；并论证所选数据类型（定点/浮点/枚举/校验码）合理性与安全性。在文档里面说明。
