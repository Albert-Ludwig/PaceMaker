# Folder File Purpose:

main.py Entry point: launches login screen and dashboard. The main file should only contains the welcome window class can call the interfaces from other files.

modules/auth.py Handles registration/login logic with password hashing

modules/dashboard.py Main DCM interface: mode selection, parameter input, status indicators

modules/storage.py Read/write JSON files for users and parameters

data/users.json Stores up to 10 registered users

data/parameters.json Stores saved parameter sets

assets/ Optional: icons, logos, style assets

# Johnson's own note: (Others pls don;t delete and I will delete it when finish)

# 10/14:

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
