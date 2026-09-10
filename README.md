# PyInstaller 快捷打包工具

图形化配置 [PyInstaller](https://pyinstaller.org/) 打包参数的小工具 —— 不用再记一长串命令行参数，勾勾选选就能把 Python 脚本打成 exe。

**Windows 专用**，纯标准库 tkinter，无第三方 GUI 依赖。

## 功能

- **可视化配置**：脚本、图标、输出路径、程序名、额外数据文件、隐藏导入模块
- **常用参数一键勾选**：`--onefile`、`--windowed`、`--noconfirm`、`--clean`、`--debug`
- **命令实时预览**：配置改一下，底部立刻显示等价命令，可一键复制到剪贴板
- **图标预览**：选好图标当场看到成品 exe 的缩略图和名称
- **后台打包 + 实时日志**：打包不卡界面，PyInstaller 的输出逐行滚动显示
- **`input()` 冲突检测**：勾了 `--windowed` 但脚本里有 `input()` / `getpass()` 时弹窗提醒。这类脚本打包后会因读不到标准输入而崩溃，工具会问你要不要自动取消 `--windowed`
- **最近文件**：常用脚本一键打开，省去每次翻目录
- **设置持久化**：表单内容自动保存，下次打开就是上次的样子

## 环境要求

- Windows
- Python 3.7 或更高（tkinter 随 Python 一起安装，无需额外操作）
- PyInstaller：`pip install pyinstaller`

## 运行

```bash
pip install pyinstaller
python Py打包工具.py
```

## 使用

1. 点「Python 文件」选中要打包的脚本
2. 按需填写图标、输出路径、程序名等；留空的项不会出现在命令里
3. 在「打包选项」里勾选需要的参数
4. 看一眼下方的命令预览，确认无误
5. 点「开始打包」，日志区会实时输出进度
6. 完成后点「打开输出文件夹」取走 exe

### 字段与参数的对应关系

| 界面字段 | 对应参数 | 说明 |
|----------|----------|------|
| Python 文件 | *(位置参数)* | 要打包的入口脚本，必填 |
| 图标 | `--icon` | 支持 `.ico` 与常见图片格式，带缩略图预览 |
| 输出路径 | `--distpath` | 成品 exe 的存放目录 |
| 额外数据文件 | `--add-data` | 格式 `源路径;目标路径`，多个用分号分隔 |
| 程序名称 | `--name` | 留空则用脚本文件名 |
| 隐藏导入模块 | `--hidden-import` | 逗号分隔，用于 PyInstaller 没能自动识别的模块 |
| 单文件模式 | `--onefile` | 打成单个 exe |
| 隐藏控制台窗口 | `--windowed` | 双击运行不弹黑框；与 `input()` 冲突 |
| 覆盖输出不询问 | `--noconfirm` | 直接覆盖旧的输出目录 |
| 清理构建文件 | `--clean` | 打包前清掉缓存 |
| 调试模式 | `--debug` | 等级可选 `all` / `imports` / `bootloader` / `noarchive` |

## 项目结构

```
Py打包工具.py              程序入口
pyinstaller_helper/
├── app.py                 主窗口控制器：组装界面、业务逻辑、弹窗交互
├── chrome.py              标题栏、状态栏、操作按钮
├── file_card.py           文件设置卡片
├── options_card.py        打包选项卡片
├── panels.py              命令预览与日志面板
├── menubar.py             菜单栏（最近文件、设置）
├── style.py               ttk 全局样式
├── command.py             参数校验与命令组装（纯逻辑）
├── build_process.py       后台打包线程，经队列向界面回传日志
├── analyzer.py            用 AST 检测脚本中的 input() / getpass()
├── icon.py                解析 .ico 并渲染为 PNG 供预览
├── history.py             最近文件历史读写
├── settings.py            表单设置读写
└── config.py              路径与配色常量
```

界面层（`chrome` / `file_card` / `options_card` / `panels` / `menubar`）只负责画界面；纯逻辑层（`command` / `analyzer` / `icon` / `history` / `settings`）不碰任何界面元素。所有弹窗集中在 `app.py`。

## 说明

- **仅支持 Windows**：用到了 `os.startfile`、`subprocess.CREATE_NO_WINDOW` 和 Win32 图标 API。
- **配置文件位置**：源码运行时存在项目根目录；打包成 exe 后改存 `%LOCALAPPDATA%\PyInstallerHelper`，与启动目录无关。
- 打包本身由 PyInstaller 完成，遇到具体报错请查阅 [PyInstaller 文档](https://pyinstaller.org/en/stable/)。
