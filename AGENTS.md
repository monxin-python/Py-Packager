# AGENTS.md

本文件为 Codex 在此仓库中工作时提供指导。

## 项目概述

PyInstaller 快捷打包工具 v3.0.0 —— 一个 **Windows 专用的 tkinter GUI 应用**，用于图形化配置 PyInstaller 打包参数、预览命令、后台执行打包并实时显示日志。

- 入口：`Py打包工具.py` → `pyinstaller_helper.app.App`
- 运行方式：`python Py打包工具.py`（需先 `pip install pyinstaller`）
- 无测试、无第三方 GUI 依赖（仅标准库 tkinter）

## 架构与模块职责

`pyinstaller_helper/` 包按「GUI 层 / 纯逻辑层」严格分离：

| 模块 | 职责 | 约束 |
|------|------|------|
| `app.py` | tkinter 主窗口控制器：组装各部件、业务逻辑、弹窗交互 | 唯一允许调用 messagebox/filedialog 的模块 |
| `style.py` | ttk 全局样式 | 仅样式配置 |
| `chrome.py` | 标题栏、状态栏、操作按钮 | 仅界面构建，不含弹窗 |
| `file_card.py` | 文件设置卡片（自带输入框变量） | 仅界面构建，不含弹窗 |
| `options_card.py` | 打包选项卡片（复选框、调试等级下拉框） | 仅界面构建，不含弹窗 |
| `panels.py` | 命令预览、打包日志面板 | 仅界面构建，不含弹窗 |
| `menubar.py` | 菜单栏（最近文件、设置） | 仅界面构建，不含弹窗 |
| `command.py` | `BuildConfig` dataclass、参数校验、命令组装、预览格式化 | 纯逻辑，不含任何弹窗 |
| `icon.py` | 用 Win32 API 从 .ico 提取图标，渲染为 PNG 字节供预览 | 纯逻辑；Windows 专用；仅标准库；失败返回 None |
| `analyzer.py` | 用 AST 检测脚本中的 `input()`/`getpass()` 调用 | 纯逻辑；避免注释/字符串误报 |
| `build_process.py` | 后台线程运行 PyInstaller，经队列向 GUI 发消息 | 不直接操作 GUI；消息 kind：`OUT`/`DONE`/`ERROR` |
| `history.py` | 最近文件历史 JSON 读写 | 纯逻辑；读写失败静默降级 |
| `settings.py` | 表单设置 JSON 读写（默认值合并、类型校验） | 纯逻辑；读写失败静默降级 |
| `config.py` | 历史/设置文件路径、配色、字体常量 | 唯一集中配置处 |

## 关键约定

- **Windows 专用**：使用了 `os.startfile`、`subprocess.CREATE_NO_WINDOW`，不要改为跨平台方案或移除 Windows 特性。
- **命令以列表组装，绝不拼字符串**：`assemble_command()` 返回参数列表交给 `subprocess.Popen`，路径含空格也能正确处理；字符串拼接仅在 `format_cmd()` 中用于预览显示。
- **GUI 线程安全**：打包在守护线程执行，所有输出经 `queue.Queue` 传递，GUI 用 `root.after(100, poll_log)` 轮询；不要在 `build_process.py` 中触碰任何 tkinter 对象。
- **编码兼容**：读取用户脚本时优先 UTF-8（含 BOM），失败回退 GBK（`analyzer.read_text_file`）。
- **历史/设置文件路径由 `config._data_dir()` 统一计算**：源码运行时固定在项目根目录；打包（`sys.frozen`）后放在 `%LOCALAPPDATA%\PyInstallerHelper`，与启动目录无关，不要改成相对当前工作目录或临时目录。
- **`--windowed` 与 `input()` 冲突**：打包前用 AST 检测并弹窗询问用户是否自动取消（`app.build_command`），保留这一交互。
- 新模块继续遵守：纯逻辑模块 docstring 注明「纯逻辑」；界面部件模块 docstring 注明「仅界面构建，不含弹窗」；弹窗一律留在 `app.py`。
- 表单状态归各卡片所有：卡片暴露 `values()` / `apply_values()`（键名与 `settings.py`、`BuildConfig` 字段一一对应），`app.py` 只做合并与转发。
