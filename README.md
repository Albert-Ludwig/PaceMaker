<!-- prettier-ignore-file -->
<!-- markdownlint-disable-file -->
<!-- eslint-disable -->

# The file description

## Files & Roles (one-liners)

- main.py
  Application entrypoint. Boots Tk, installs a global error hook, and switches between Login and Dashboard. Keeps startup “thin”.

- auth.py
  Authentication utilities (e.g., login_account, logout_account). Pure logic; no UI.

- dashboard.py
  Main GUI shell after login (DashboardWindow). Wires feature windows (Help, Egram), menus, and top-level actions.

- Help_Window.py
  Standalone Help window (HelpWindow). Loads help topics from JSON and renders “Param description” & “Mode description”.

- EGdiagram.py
  Egram (ECG/EGM) viewer window. Manages data stream (thread/queue), start/stop/clear, y-zoom display (X0.5/X1/X2), and canvas rendering.

- mode_config.py
  Parameter catalogue and pacing modes (e.g., ParamEnum, MODES, range/type defaults). Single source of truth for parameter defaults.

- ParamOps.py
  Parameter operations layer (e.g., ParameterManager or helpers): read/apply/validate parameters, fetch defaults from mode_config, persist to storage if needed.

## Class diagram

```text
+------------------+           uses            +-------------------+
|      App         |-------------------------->|  DashboardWindow  |
| (main.py)        |                          | (dashboard.py)    |
+------------------+                          +-------------------+
| - root: Tk       |                          | - root: Tk        |
| - _dashboard     |                          | - username: str   |
| - _login_win     |                          | - help_window     |
+------------------+                          +-------------------+
| +run()           |                          | +open_help_window()|
| +_show_login()   |                          | +open_egram()      |
| +_open_dashboard()                          |                   |
+------------------+                          +-------------------+
        |                                                |
        | opens                                          | opens
        v                                                v
+-------------------+                          +-------------------+
|    HelpWindow     |                          |    EgramWindow    |
| (Help_Window.py)  |                          | (EGdiagram.py)    |
+-------------------+                          +-------------------+
| - topics: dict    |                          | - controller      |
| - content_area    |                          | - canvas(view)    |
+-------------------+                          +-------------------+
| +update_content() |                          | +start_egram()    |
| +_display_param() |                          | +stop_egram()     |
| +_display_mode()  |                          | +clear_egram()    |
+-------------------+                          +-------------------+
                                                     |
                                                     | owns
                                                     v
                                           +-------------------+
                                           |   EgramView       |
                                           | (canvas drawing)  |
                                           +-------------------+
                                           | +render(model)    |
                                           | +zoom label (X…)  |
                                           +-------------------+
                                                     |
                                                     | pulls data from
                                                     v
                                           +-------------------+
                                           | EgramController   |
                                           | (thread/queue)    |
                                           +-------------------+

+-------------------+         used by          +-------------------+
|   ParamEnum       |<-------------------------| ParameterManager  |
| (mode_config.py)  |                          | (ParamOps.py)     |
+-------------------+                          +-------------------+
| +get_default_...()|                          | +apply/update     |
| MODES, ranges     |                          | +validate         |
+-------------------+                          +-------------------+

+-------------------+
|   auth.py         |
+-------------------+
| +login_account()  |
| +logout_account() |
+-------------------+
```

Notes
• EgramController/EgramView naming follows your current EGdiagram sections (controller thread + canvas).
• ParameterManager is the typical abstraction in ParamOps.py; if your file exposes functions instead, treat it as the same layer in the diagram.

## Structure chart

```text
main.py
└─ App.run()
├─ \_show_login() ──(calls)──► auth.login_account(...) [if auth is present]
└─ \_open_dashboard(username)
└─ DashboardWindow(root, username) [dashboard.py]
├─ open_help_window()
│ └─ HelpWindow(root) [Help_Window.py]
│ └─ load help JSON from /data and render topics
│
├─ open_egram()
│ └─ EgramWindow(root) [EGdiagram.py]
│ ├─ start_egram()
│ │ └─ EgramController.start() → background thread feeds queue
│ ├─ stop_egram() └─ EgramController.stop() (join/cleanup)
│ └─ clear_egram() └─ clear buffers + redraw EgramView
│
└─ parameter ops (when needed)
├─ ParamOps.ParameterManager (or helper funcs) [ParamOps.py]
│ └─ uses mode_config.ParamEnum.get_default_values()
└─ mode_config.ParamEnum / MODES [mode_config.py]
```

## Quick coherence/coupling checklist (why this is clean)

- main.py only boots, routes, and handles global errors → high cohesion (startup) / low coupling (no business details).

- dashboard.py composes UI and opens sub-windows; it does not re-implement help/egram logic → clear boundaries.

- Help_Window.py focuses on rendering help; JSON reading is isolated (if you moved it to a loader) → easy reuse.

- EGdiagram.py keeps data thread, queue, and canvas together → one place to maintain streaming & drawing.

- mode_config.py is the single source for modes & defaults → other modules query, not copy.

- ParamOps.py centralizes parameter validation/apply → UI just calls it, no duplicated logic.

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
6. EGdiagram，目前为底层实现，leaf module，后期可能会用到 comm。
7. Comm，目前暂时未实现

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

## 10/18

新增 Help_Window 函数，这样就可以用 dashboard 直接调用 Help_Window。
修改了 EGdiagram 里面的 update_button 方法。
