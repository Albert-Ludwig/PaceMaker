# Folder File Purpose:

main.py Entry point: launches login screen and dashboard. The main file should only contains the welcome window class can call the interfaces from other files.

modules/auth.py Handles registration/login logic with password hashing

modules/dashboard.py Main DCM interface: mode selection, parameter input, status indicators

modules/storage.py Read/write JSON files for users and parameters

data/users.json Stores up to 10 registered users

data/parameters.json Stores saved parameter sets

assets/ Optional: icons, logos, style assets

# Johnson's own note: (Others pls don;t delete and I will delete it when finish)

## 10/14:

auth.py 记录所有的和用户登陆相关的操作，dashboard 负责界面操作（生成按钮，跳转），mode_config 记录数据类型，以及 getter 和 setter，ParamOps 负责和参数相关的操作，包括生成选择模式和修改参数的界面，dashboard 直接调用。main 只有一个初始化的实现，剩下都是调用已有接口。
注：对于提醒 message，我没有单独创建一个 module，而是集成到各个部分里面了。

Relational Hierarchy:

1. mode_config，底层，leaf module。
2. auth.py，底层，不需要其他 module。
3. ParamOps，需要用 mode_config。
4. dashboard，需要用 mode_config 和 ParamOps。
5. main，需要用到 auth 和 dashboard。

改动：

1. 目前不需要 storage 和 validation，已经删除。
2. 新增两个 json：mode 和 param help，存储 mode 和 parameter 信息，并且在 dashboard 被调用。
3. dashboard 新增 help widget，并且新增相应的 class，有专门函数可以把 json 转换为文档形式。初步已完成 help window。

## 10/15

增加指示灯 out of range 和 noise，定性为 warning，并且新增 communication 和 EG 文件，用来定义 serial communication 和 EG 画图。

## 10/16

实现了 EGdiagram，在 dashboard 新增 def open_egram_window(self):，以及 self.egram_window = None 作为初始化。

### 记录：

- EgramModel

功能定位：数据模型层（Model）

保存并管理所有心电信号（Atrial、Ventricular、Surface ECG）的数据缓存。

通过 deque 实现固定长度的滚动数据窗口（支持历史平移）。

维护显示参数：时间窗口长度、采样率、增益等。

提供 append_batch() 接口供控制器批量更新数据。

- EgramController

功能定位：控制层（Controller）

负责在后台线程中从数据源持续读取批次信号。

利用 tkinter.after() 定时在主线程中刷新画面（调用 view.render()）。

实现数据从源 → 模型 → 视图的流转控制。

提供 start() / stop() 方法控制数据流生命周期。

- EgramView

功能定位：视图层（View）

使用 Tkinter Canvas 绘制实时波形、网格、坐标轴与刻度。

支持鼠标交互：

左键拖动左右平移；

双击回到实时末端。

支持波形缩放（X0.5 / X1 / X2）并在右上角显示当前倍率。

仅负责显示，不保存数据；通过 render(model) 从模型读取数据绘制。

- EgramWindow

功能定位：窗口与界面层（UI 管理）

创建完整的用户界面，包括按钮、复选框和波形画布。

管理 Start / Stop / Clear 按钮的状态与逻辑：

Start 后禁用 Start 与 Clear，仅允许 Stop；

Stop 后恢复 Start 与 Clear；

Clear 前弹出确认提示。

管理关闭事件：运行中关闭会弹出确认是否停止并退出。

负责协调 EgramModel、EgramController 与 EgramView。

- MockEgramSource

功能定位：数据源模拟（用于测试）

生成三路模拟心电信号（Atrial、Ventricular、Surface ECG）。

以固定采样率产生正弦波叠加随机噪声，周期性 yield 数据批次。

接口与未来的 SerialEgramSource 一致，可无缝替换。

MockEgramSource 使用说明总结：
在当前版本的 EGdiagram.py 中，MockEgramSource 仅用于提供模拟信号数据，方便在无真实设备连接的情况下测试整体界面和绘图逻辑。
该类在文件底部定义，并在 EgramWindow.**init**() 中被实例化：

self.source = MockEgramSource()

这是代码中唯一显式使用 MockEgramSource 的地方。
程序运行时，EgramWindow 创建该模拟数据源并传递给 EgramController；控制器随后调用其 stream() 方法持续生成数据批次，通过 EgramModel 缓存并由 EgramView 实时绘制波形。

换言之，MockEgramSource 负责模拟心电信号输入，其输出经过控制器—模型—视图链路完成实时显示。
未来若接入真实串口通信，只需在 EgramWindow.**init**() 中将

self.source = MockEgramSource()

替换为

self.source = SerialEgramSource(...)

即可完全替换数据源逻辑，而无需修改其他模块
